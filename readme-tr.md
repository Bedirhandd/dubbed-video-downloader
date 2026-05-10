# YouTube Dublajlı Video İndirici

[yt-dlp](https://github.com/yt-dlp/yt-dlp) ve [FFmpeg](https://ffmpeg.org/) kullanarak YouTube videolarını belirli bir **dublaj diliyle** (örneğin Türkçe, İngilizce veya İspanyolca) indirmenizi sağlayan basit bir Python betiği.

Script şu durumlar için kullanılabilir:

- **Dublajlı YouTube videolarını** indirmek (çok dilli ses desteği).
- Videoyu `.mkv` formatında kaydedip seçilen ses parçasıyla birleştirmek.
- Dosyaları **dil, kanal ve başlık** klasör yapısına göre düzenlemek.
- Çoklu ses parçası sunan kanallarla çalışmak (örneğin MrBeast).

Betik videoları `.mkv` formatında kaydeder ve şu klasör yapısını oluşturur:

```text
Videos/<dil>/<kanal>/<başlık>/<başlık>.mkv

Örnek:
Videos/tr/MrBeast/World_s_Deadliest_Obstacle_Course/World_s_Deadliest_Obstacle_Course.mkv
```

## Test Edilen Ortam

- Python `3.12.3`
- yt-dlp `2026.3.17`
- yt-dlp-ejs `0.8.0`
- Node.js `22.22.2`
- Bağımlılık yönetimi için [uv](https://docs.astral.sh/uv/)

## Gereksinimler

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Python `>=3.10` (uv proje `.python-version` dosyasını kullanabilir)
- yt-dlp'nin YouTube JavaScript çözümleyicisi için sistem `PATH` içinde Node.js
- **FFmpeg** sistem `PATH` içinde olmalı veya betikte `FFMPEG_PATH` ile tam yol belirtilmeli

Node.js ve FFmpeg kurulu mu kontrol etmek için:

```bash
node --version
ffmpeg -version
```

Yüklü değilse resmi siteden indirebilirsiniz: [https://ffmpeg.org/](https://ffmpeg.org/)

## Kurulum

Repoyu klonlayın veya script dosyasını indirin, sonra gerekirse uv kurun:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows PowerShell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Proje ortamını senkronize edin:

```bash
uv sync
```

uv `.venv/` klasörünü oluşturur ve bağımlılıkları `pyproject.toml` ile `uv.lock` üzerinden kurar.
Projede `yt-dlp-ejs` bağımlılığı bulunur; YouTube formatlarını ve dublajlı sesleri tam görebilmek için Node.js yine de gereklidir.

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

- `DUB_LANGUAGE`: istediğiniz dublaj dil kodunu girin (`"tr"`, `"en"`, vb.).
- `FFMPEG_PATH`: FFmpeg sistem `PATH` içinde değilse tam yolunu yazın.
- `VIDEO_URLS`: indirmek istediğiniz YouTube linklerini ekleyin.

## Kullanım

Script'i uv ile çalıştırın:

```bash
uv run script.py
```

Betik şu işlemleri yapar:

1. Videoda istenen dublaj dili mevcut mu kontrol eder.
2. Dil yoksa hata verir ve mevcut dillerin listesini gösterir.
3. Videoyu ve seçilen ses parçasını indirir.
4. Bunları `.mkv` dosyasında birleştirir.
5. Dosyayı ilgili klasör yapısına kaydeder.

## Bağımlılıkları Güncelleme

yt-dlp'yi uv yönetimli proje içinde güncellemek için:

```bash
uv lock --upgrade-package yt-dlp
uv lock --upgrade-package yt-dlp-ejs
uv sync
```

Bağımlılık sürümleri değiştiğinde güncellenen `uv.lock` dosyasını commit edin. `uv.lock` dosyasını elle düzenlemeyin.

## Notlar

- `WARNING: Unable to download format 616. Skipping...` gibi uyarılar normaldir. yt-dlp farklı kalite ID'lerini dener, bazıları çalışmayabilir. Çalışan formata otomatik düşer.
- Çıktı klasör yapısını değiştirmek isterseniz `outtmpl()` fonksiyonunu düzenleyebilirsiniz.

## Yasal Uyarı

- Bu betik yalnızca **kişisel ve eğitim amaçlı kullanım** için sağlanmaktadır.
- YouTube'un [Kullanım Şartları](https://www.youtube.com/static?template=terms) ve içerik üreticilerin haklarına saygı gösterin.
- İzin alınmadan video indirip yeniden paylaşmak telif haklarını ihlal edebilir.

## Anahtar Kelimeler

*YouTube video indirme, YouTube dublaj indirici, çok dilli ses, yt-dlp, ffmpeg, mkv, YouTube dublajlı video indirme, YouTube dublajlı video indir, Python YouTube downloader*
