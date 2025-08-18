# YouTube Dublajlı Video İndirici

[yt-dlp](https://github.com/yt-dlp/yt-dlp) ve [FFmpeg](https://ffmpeg.org/) kullanarak YouTube videolarını belirli bir ****dublaj diliyle**** (örneğin Türkçe, İngilizce, İspanyolca) indirmenizi sağlayan basit bir Python betiği. Zamanında aramıştım ve bulamamıştım, belki sizin işinize yarar :)

Scripti şu durumlar için kullanılabilir:

- ****Dublajlı YouTube videolarını**** indirmek (çok dilli ses desteği).
- Videoyu `.mkv` formatında kaydedip seçilen ses parçasıyla birleştirmek.
- Dosyaları ****dil, kanal ve başlık**** klasör yapısına göre düzenlemek.
- Çoklu ses parçası sunan kanallarla çalışmak (örneğin MrBeast).

Yani kısaca ****YouTube çok dilli / dublajlı video indirici****.

Betik videoları `.mkv` formatında kaydeder ve şu klasör yapısını oluşturur:

```

Videos/<dil>/<kanal>/<başlık>/<başlık>.mkv
```
Örnek:
```
Videos/tr/MrBeast/World_s_Deadliest_Obstacle_Course/World_s_Deadliest_Obstacle_Course.mkv
```

---

## Test Edilen Ortam

- Python `3.11.4`
- yt-dlp `2025.8.11`
- FFmpeg `N-117058-gceb471cfde-20240916`

---

## Gereksinimler

- ****Python**** (>= 3.10 önerilir)
- ****FFmpeg**** (sistem PATH’ine eklenmiş olmalı veya betikte tam yol belirtilmeli)

FFmpeg kurulu mu kontrol etmek için:

```bash
ffmpeg -version
````

Yüklü değilse resmi siteden indirebilirsiniz:
👉 [https://ffmpeg.org/](https://ffmpeg.org/)

---

## Kurulum

1. Repoyu klonlayın veya script dosyasını indirin.

2. ****Sanal ortam oluşturun**** (önerilir):

```bash
python -m venv env
```

Aktifleştirme:

* Windows:

  ```bash
  env\Scripts\activate
  ```
* Linux / macOS:

  ```bash
  source env/bin/activate
  ```

3. ****Gerekli paketleri yükleyin****:

```bash
pip install -r requirements.txt
```

`requirements.txt` içeriği:

```
yt-dlp==2025.8.11
```

---

## Yapılandırma

`script.py` dosyasını açın ve gerekirse düzenleyin:

```python
DUB_LANGUAGE = "tr"   # İndirilecek dublaj dili, örn: "tr", "en"
FFMPEG_PATH = None    # Örn: "C:/ffmpeg/ffmpeg.exe"
                      # None bırakırsanız yt-dlp PATH üzerinden bulur
VIDEO_URLS = [
    "https://www.youtube.com/watch?v=EXAMPLE1",
    "https://www.youtube.com/watch?v=EXAMPLE2",
]
```

* `DUB_LANGUAGE`: istediğiniz dublaj dil kodunu girin (`"tr"`, `"en"`, vb.)
* `FFMPEG_PATH`: FFmpeg sistem PATH’te değilse tam yolunu yazın.
* `VIDEO_URLS`: indirmek istediğiniz YouTube linklerini ekleyin (video, playlist, kanal olabilir).

---

## Kullanım

Script’i çalıştırın:

```bash
python script.py
```

Betik şu işlemleri yapar:

1. Videoda istenen dublaj dili mevcut mu kontrol eder.

   * Yoksa hata verir ve mevcut dillerin listesini gösterir.
2. Videoyu ve seçilen ses parçasını indirir.
3. Bunları `.mkv` dosyasında birleştirir.
4. Dosyayı ilgili klasör yapısına kaydeder.

---

## Notlar

* `WARNING: Unable to download format 616. Skipping...` gibi uyarılar normaldir.
  yt-dlp farklı kalite ID’lerini dener, bazıları çalışmayabilir. Çalışan formata otomatik düşer.

* Çıktı klasör yapısını değiştirmek isterseniz `outtmpl()` fonksiyonunu düzenleyebilirsiniz.

---

## Yasal Uyarı

* Bu betik yalnızca ****kişisel ve eğitim amaçlı kullanım**** için sağlanmaktadır.
* YouTube’un [Kullanım Şartları](https://www.youtube.com/static?template=terms) ve içerik üreticilerin haklarına saygı gösterin.
* İzin alınmadan video indirip yeniden paylaşmak telif haklarını ihlal edebilir.

---

## Anahtar Kelimeler

_*YouTube video indirme, YouTube dublaj indirici, çok dilli ses, yt-dlp, ffmpeg, mkv, YouTube dublajlı video indirme, YouTube dublajlı video indir, Python YouTube downloader*_