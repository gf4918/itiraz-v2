# Aile Hekimliği Performans İtiraz Formu Doldurucu (Ek-2 & Ek-8)

Bu proje, Aile Hekimlerinin aylık performans kesintilerine karşı sunacakları **Ek-2 Performans İtiraz Formu** ile **Ek-8 Bağışıklama Hizmeti Bilgilendirme Onam Formu** belgelerini web arayüzü üzerinden hızlı, hatasız ve otomatik olarak doldurmalarını sağlayan, tamamen istemci tarafında (tarayıcıda) çalışan bir web uygulamasıdır.

## 🚀 Öne Çıkan Özellikler

1. **Tamamen Sunucusuz (Serverless / Client-Side)**:
   - Tüm işlemler tarayıcınızda gerçekleşir. Verileriniz hiçbir sunucuya yüklenmez, gizlilik ve veri güvenliği 100% korunur.
   - Excel/Word otomasyonu için harici kütüphane veya backend ihtiyacı yoktur.

2. **Dinamik ve Akıllı Arayüz**:
   - **Koşullu Alan Gösterimi**: Kişi bilgileri alanındaki opsiyonel kutular, seçilen itiraz konularına göre dinamik olarak açılır/gizlenir (örn: Gebe İzlemi seçilirse SAT alanı açılır, Lohusa İzlemi seçilirse doğum tarihi alanı açılır).
   - **Otomatik Temizleme**: Bir itiraz konusu kapatıldığında ilgili form alanı otomatik olarak gizlenir ve eski veriler temizlenerek çıktı belgesinde kirlilik yaratması önlenir.

3. **Aile Hekimliği Birimi & Doktor Seçim Havuzu (Config)**:
   - Doktorların her seferinde Birim No, Hekim Adı ve Hekim T.C. bilgilerini elle yazmasına gerek yoktur.
   - Tanımlanan havuzdan (`AH_UNITS_CONFIG`) ilgili birim seçildiğinde hekimin adı, T.C. Kimlik numarası ve Aile Sağlığı Çalışanı (ASÇ) adı otomatik olarak yüklenir ve tüm belgelere yansıtılır.

4. **Çoklu Çıktı Desteği**:
   - **Word (.docx)** formatında orijinal şablon yapısını koruyarak indirme.
   - **PDF** formatında indirme ve doğrudan **Yazdır (Print)** penceresi açma.
   - Tüm çıktılar **A4 tek sayfa** sınırlarına tam sığacak şekilde tasarlanmıştır. İtiraz nedeni uzun yazılsa dahi taşmalar otomatik olarak engellenir.

---

## 🛠️ Nasıl Çalıştırılır?

Projeyi çalıştırmak için herhangi bir kuruluma veya kuruluma ihtiyaç yoktur. İki yöntemle çalıştırabilirsiniz:

### Yöntem 1: Doğrudan Açarak (En Basit)
- Proje klasöründeki `index.html` dosyasına çift tıklayarak tarayıcınızda açabilirsiniz.

### Yöntem 2: Yerel Web Sunucusu ile (Önerilen)
Uygulamanın tam performanslı çalışması ve bazı tarayıcılardaki CORS kısıtlamalarını engellemek için yerel bir sunucu kurabilirsiniz. Terminalde proje dizinine gidip şu komutlardan birini çalıştırın:

**Python ile:**
```bash
python -m http.server 8000
```
Ardından tarayıcınızdan `http://localhost:8000/` adresine gidiniz.

---

## ⚙️ Hekim / Birim Bilgilerini Özelleştirme

Sık kullanılan doktor listesini ve birimleri kalıcı olarak eklemek için `index.html` dosyasını bir metin editörüyle açıp en üstteki `AH_UNITS_CONFIG` dizisini düzenlemeniz yeterlidir:

```javascript
const AH_UNITS_CONFIG = [
    {
        label: "27.02.277 - Dr. SADIK BAHCİVAN",
        birimNo: "27.02.277",
        hekimAdi: "Dr. SADIK BAHCİVAN",
        hekimTc: "63946395432",
        ascAdi: "A.S.Ç. ÖZLEM BULUT"
    },
    {
        label: "27.02.278 - Dr. AHMET YILMAZ",
        birimNo: "27.02.278",
        hekimAdi: "Dr. AHMET YILMAZ",
        hekimTc: "12345678901",
        ascAdi: "A.S.Ç. NURTEN CAN"
    }
];
```

---

## 📂 Teknik Altyapı ve Çalışma Mantığı

Uygulamanın arka planında, Word şablonlarının XML yapısını doğrudan manipüle eden yenilikçi bir yöntem kullanılmıştır:

### 1. Şablonların Hazırlanması (DOCX -> XML -> Base64)
- Orijinal boş `.docx` şablonları (Ek-2 ve Ek-8), aslında birer `.zip` arşividir. Bu arşivler açılarak içlerindeki metin ve biçimlendirme kurallarını barındıran `word/document.xml` dosyaları incelenmiştir.
- Değişken olması gereken alanlar (örn: `{{adi_soyadi}}`, `{{birim_no}}`, `{{hekim_imza_tarih}}`) belirlenmiş ve XML yapısına placeholder olarak yerleştirilmiştir.
- Biçimlendirme sırasında MS Word'ün oluşturduğu gereksiz XML düğümleri temizlenerek etiket bütünlüğü (`{{placeholder}}` yapısının bölünmemesi) sağlanmıştır.
- Hazırlanan şablon dosyaları, Javascript tarafından doğrudan okunabilmesi amacıyla base64 formatına dönüştürülerek `template_docx.js` ve `template_ek8_docx.js` dosyalarına kaydedilmiştir.

### 2. Dinamik Doldurma ve Sıkıştırma (JSZip)
- Kullanıcı arayüzde bilgileri girip "Word İndir" butonuna bastığında:
  1. İlgili şablonun base64 verisi `atob` ile binary veriye dönüştürülür.
  2. `JSZip` kütüphanesi yardımıyla bu binary veri bir zip arşivi olarak belleğe yüklenir.
  3. `word/document.xml` dosyası string olarak okunur.
  4. Kullanıcının formda doldurduğu alanlar, XML içindeki placeholder'lar ile (`.split().join()` yöntemiyle) değiştirilir.
  5. Güncellenmiş XML dosyası tekrar zip içine yazılır ve yeni bir `.docx` dosyası olarak tarayıcı üzerinden kullanıcıya indirtilir.

### 3. PDF ve Yazdırma Şablonları (HTML5 & CSS)
- Uygulama, Word belgesinin görsel tasarımını birebir taklit eden gizli bir HTML yazdırma şablonuna sahiptir.
- CSS `@media print` kuralları kullanılarak tarayıcının yazdırma penceresinde belgenin tam A4 boyutunda, taşma yapmadan ve marjinleri korunmuş şekilde çıkması sağlanmıştır.
- PDF çıktısı için `html2pdf.js` kütüphanesi kullanılarak istemci tarafında ekran görüntüsü tabanlı, yüksek kaliteli PDF dönüşümü sağlanmaktadır.

---

## 📝 Ek-8 Bağışıklama Onam Formu İyileştirmeleri
Ek-8 "Bağışıklama Hizmeti Bilgilendirme Onam Formu" üzerinde yapılan kritik güncellemeler:
- **Hizalama ve Boşluklar**: XML düzeyinde yapılan düzeltmelerle, isimler ve T.C. kimlik numaralarının bitişik çıkması sorunu giderilmiştir. İsimler ile T.C. numaraları arasında doğal tek karakterlik boşluklar bırakılmıştır.
- **İmza Alanları ve Tarih**: Formun altındaki imza bloğunda, hem **Aile Sağlığı Çalışanı** hem de **Aile Hekimi** imza çizgilerinin üzerine tarih alanı eklenmiştir. Arayüzden girilen imza tarihi her iki tarafa da otomatik ve eşzamanlı olarak yazılmaktadır.

## 📄 Lisans
Bu proje kamu yararına ve Aile Hekimlerinin bürokratik süreçlerini kolaylaştırmak amacıyla açık kaynak olarak geliştirilmiştir. Dilediğiniz gibi kullanabilir, geliştirebilir ve dağıtabilirsiniz.
