import http.server
import socketserver
import urllib.parse
import json
import pyodbc
import socket
import sys

PORT = 8000
DB_NAME = "TestDB"
DB_USER = "sa"
DB_PASS = "T902HDA_42"

class PatientDbHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        
        # Check API routes
        if parsed_url.path == '/api/patient':
            self.handle_api_patient(parsed_url)
        elif parsed_url.path == '/api/config':
            self.handle_api_config()
        else:
            # Serve static files as usual
            super().do_GET()

    def handle_api_config(self):
        import os
        config_path = 'config.txt'
        config_data = []
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        parts = [p.strip() for p in line.split('|')]
                        if len(parts) >= 5:
                            birim_no = parts[0]
                            hekim_adi = parts[1]
                            hekim_tc = parts[2]
                            asc_adi = parts[3]
                            computer_name = parts[4]
                            label = parts[5] if len(parts) > 5 else f"{birim_no} - Dr. {hekim_adi}"
                            
                            config_data.append({
                                "label": label,
                                "birimNo": birim_no,
                                "hekimAdi": hekim_adi,
                                "hekimTc": hekim_tc,
                                "ascAdi": asc_adi,
                                "computerName": computer_name
                            })
            except Exception as e:
                print(f"Error parsing config.txt: {e}", file=sys.stderr)
        
        self.send_json_response(200, config_data)

    def handle_api_patient(self, parsed_url):
        query_params = urllib.parse.parse_qs(parsed_url.query)
        tc_number = query_params.get('tc', [None])[0]
        computer_name = query_params.get('computer', [None])[0]

        if not tc_number:
            self.send_json_response(400, {"error": "T.C. Kimlik Numarası (tc) parametresi eksik."})
            return

        # Default to local computer name if none provided
        if not computer_name:
            computer_name = socket.gethostname()

        # Build server string (ComputerName\HIZIR)
        server_instance = f"{computer_name}\\HIZIR"
        
        # Connect to DB
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server_instance};"
            f"DATABASE={DB_NAME};"
            f"UID={DB_USER};"
            f"PWD={DB_PASS};"
            f"TrustServerCertificate=yes;"
            f"Connection Timeout=5;"
        )

        try:
            print(f"Connecting to database on {server_instance}...")
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            
            # Query to fetch patient + phone + address + latest SAT (pregnancy notification date)
            query = """
                SELECT TOP 1 
                    k.HASTA_KIMLIK_NO, k.AD, k.SOYAD, k.DOGUM_TARIHI, k.ANNE_KIMLIK_NO,
                    t.TELEFON,
                    a.BIRLESTIRILMIS_ADRES,
                    (
                        SELECT TOP 1 gb.SON_ADET_TARIHI
                        FROM GP_GEBELIK_BILDIRIM gb
                        JOIN GP_MUAYENE m ON m.MUAYENE_ID = gb.MUAYENE
                        JOIN GP_HASTA_KABUL hk ON hk.HASTA_KABUL_ID = m.HASTA_KABUL
                        WHERE hk.HASTA_KAYIT = k.HASTA_KAYIT_ID AND gb.SON_ADET_TARIHI IS NOT NULL
                        ORDER BY gb.GEBELIK_BILDIRIM_ID DESC
                    ) AS SON_ADET_TARIHI
                FROM GP_HASTA_KAYIT k
                LEFT JOIN GP_HASTA_OZLUK o ON o.HASTA_KAYIT = k.HASTA_KAYIT_ID
                LEFT JOIN DTY_HASTA_OZLUK_TELEFON t ON t.HASTA_OZLUK = o.HASTA_OZLUK_ID
                LEFT JOIN DTY_HASTA_OZLUK_ADRES a ON a.HASTA_OZLUK = o.HASTA_OZLUK_ID
                WHERE k.HASTA_KIMLIK_NO = ?
                ORDER BY t.VARSAYILAN DESC, a.VARSAYILAN DESC
            """
            
            cursor.execute(query, tc_number)
            row = cursor.fetchone()
            
            if row:
                cols = [desc[0] for desc in cursor.description]
                data = dict(zip(cols, row))
                
                # Format dates and numbers nicely
                if data.get('DOGUM_TARIHI'):
                    data['DOGUM_TARIHI'] = data['DOGUM_TARIHI'].isoformat() # YYYY-MM-DD
                
                if data.get('SON_ADET_TARIHI'):
                    data['SON_ADET_TARIHI'] = str(data['SON_ADET_TARIHI'])[:10] # YYYY-MM-DD
                
                # Format phone number if exists
                if data.get('TELEFON'):
                    data['TELEFON'] = str(data['TELEFON'])
                    if len(data['TELEFON']) == 10 and not data['TELEFON'].startswith('0'):
                        data['TELEFON'] = '0' + data['TELEFON']
                
                conn.close()
                self.send_json_response(200, data)
            else:
                conn.close()
                self.send_json_response(404, {"error": "Hasta bulunamadı."})
                
        except Exception as e:
            print(f"Database error: {e}", file=sys.stderr)
            self.send_json_response(500, {
                "error": f"Veritabanına bağlanılamadı ({server_instance}).",
                "details": str(e)
            })

    def send_json_response(self, status_code, data):
        response_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(response_bytes)))
        # Enable CORS for local development comfort
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response_bytes)

def main():
    # Make sure we run in the correct workspace directory
    # so index.html and other static files can be served
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Start the server
    handler = PatientDbHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Server is running on http://localhost:{PORT}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            sys.exit(0)

if __name__ == "__main__":
    main()
