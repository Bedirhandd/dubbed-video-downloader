# YouTube Dublajlı Video İndirici

[yt-dlp](https://github.com/yt-dlp/yt-dlp) ve [FFmpeg](https://ffmpeg.org/) kullanarak YouTube videolarını belirli bir **dublaj diliyle** (örneğin Türkçe, İngilizce veya İspanyolca) indirmenizi sağlayan Python CLI aracı.

Araç şu durumlar için kullanılabilir:

- **Dublajlı YouTube videolarını** indirmek (çok dilli ses desteği).
- Videoyu `.mkv` formatında kaydedip seçilen ses parçasıyla birleştirmek.
- Dosyaları **dil, kanal ve başlık** klasör yapısına göre düzenlemek.
- Çoklu ses parçası sunan kanallarla çalışmak (örneğin MrBeast).

CLI videoları `.mkv` formatında kaydeder ve şu klasör yapısını oluşturur:

```text
<çıktı-klasörü>/<dil>/<kanal>/<başlık>/<başlık>.mkv

Örnek:
~/Downloads/dbdvdl-output/tr/MrBeast/World_s_Deadliest_Obstacle_Course/World_s_Deadliest_Obstacle_Course.mkv
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
- **FFmpeg** sistem `PATH` içinde olmalı veya config dosyasında belirtilmeli

Node.js ve FFmpeg kurulu mu kontrol etmek için:

```bash
node --version
ffmpeg -version
```

Yüklü değilse resmi siteden indirebilirsiniz: [https://ffmpeg.org/](https://ffmpeg.org/)

## Kurulum

Repoyu klonlayın, sonra gerekirse uv kurun:

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

## Kullanım

CLI'ı uv ile kullanın:

```bash
uv run dbdvdl --help
uv run dbdvdl init
uv run dbdvdl doctor
uv run dbdvdl langs "https://www.youtube.com/watch?v=EXAMPLE"
uv run dbdvdl download "https://www.youtube.com/watch?v=EXAMPLE" --lang tr
```

`langs` veya `download` kullanmadan önce gerekli kullanıcı config dosyasını oluşturun:

```bash
uv run dbdvdl init
```

Bu komut şuraya yazar:

```text
~/.config/dubbed-video-downloader/config.yaml
```

İçerik:

```yaml
output_dir: ~/Downloads/dbdvdl-output
ffmpeg_path: ffmpeg
```

`ffmpeg_path: ffmpeg` FFmpeg'i sistem `PATH` içinden bulur. İsterseniz bunun yerine mutlak executable yolu verebilirsiniz.

Birden fazla URL ve opsiyonel çıktı/FFmpeg ayarları verebilirsiniz:

CLI config içindeki `output_dir` altına kaydeder. `--output-dir` verirseniz
mutlak yol kullanın; `~` desteklenir. CLI seçenekleri o çalıştırma için config
değerlerini ezer.

```bash
uv run dbdvdl download \
  "https://www.youtube.com/watch?v=EXAMPLE1" \
  "https://www.youtube.com/watch?v=EXAMPLE2" \
  --lang en \
  --output-dir ~/Downloads/dbdvdl-output \
  --ffmpeg-path /path/to/ffmpeg
```

Araç şu işlemleri yapar:

1. Videoda istenen dublaj dili mevcut mu kontrol eder.
2. Dil yoksa hata verir ve mevcut dillerin listesini gösterir.
3. Videoyu ve seçilen ses parçasını indirir.
4. Bunları `.mkv` dosyasında birleştirir.
5. Dosyayı `<çıktı-klasörü>/<dil>/<kanal>/<başlık>/` klasör yapısına kaydeder.

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
- Çıktı klasörünü değiştirmek için `--output-dir` kullanabilirsiniz.

## Yasal Uyarı

- Bu araç yalnızca **kişisel ve eğitim amaçlı kullanım** için sağlanmaktadır.
- YouTube'un [Kullanım Şartları](https://www.youtube.com/static?template=terms) ve içerik üreticilerin haklarına saygı gösterin.
- İzin alınmadan video indirip yeniden paylaşmak telif haklarını ihlal edebilir.

## Anahtar Kelimeler

*YouTube video indirme, YouTube dublaj indirici, çok dilli ses, yt-dlp, ffmpeg, mkv, YouTube dublajlı video indirme, YouTube dublajlı video indir, Python YouTube downloader*
