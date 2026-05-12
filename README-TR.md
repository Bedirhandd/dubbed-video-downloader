# YouTube Dublajlı Video İndirici

[yt-dlp](https://github.com/yt-dlp/yt-dlp) ve [FFmpeg](https://ffmpeg.org/) kullanarak YouTube video veya seslerini belirli bir **dublaj diliyle** (örneğin Türkçe, İngilizce veya İspanyolca) indirmenizi sağlayan Python CLI aracı.

Araç şu durumlar için kullanılabilir:

- **Dublajlı YouTube videolarını** indirmek (çok dilli ses desteği).
- Video indirmelerini seçilen dublajlı ses parçasıyla `.mkv` olarak kaydetmek.
- Ses indirmelerini seçilen dublajlı ses akışının kendi formatında kaydetmek.
- Dosyaları **dil, kanal ve başlık** klasör yapısına göre düzenlemek.
- Çoklu ses parçası sunan kanallarla çalışmak (örneğin MrBeast).

CLI, video modundaki indirmeleri `.mkv` formatında kaydeder ve şu klasör
yapısını oluşturur:

```text
<çıktı-klasörü>/<dil>/<kanal>/<başlık>/<başlık>.mkv

Örnek:
~/Downloads/dbdvdl-output/tr/MrBeast/World_s_Deadliest_Obstacle_Course/World_s_Deadliest_Obstacle_Course.mkv
```

Ses modundaki indirmeler aynı klasör yapısını kullanır ve yt-dlp'nin seçtiği
`.webm` veya `.m4a` gibi doğal ses uzantısını korur.

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
uv run dbdvdl config show
uv run dbdvdl doctor
uv run dbdvdl langs "https://www.youtube.com/watch?v=EXAMPLE"
uv run dbdvdl qualities "https://www.youtube.com/watch?v=EXAMPLE"
uv run dbdvdl download "https://www.youtube.com/watch?v=EXAMPLE"
uv run dbdvdl download "https://www.youtube.com/watch?v=EXAMPLE" --mode audio
uv run dbdvdl download "https://www.youtube.com/watch?v=EXAMPLE" --video-quality 720p
uv run dbdvdl download "https://www.youtube.com/watch?v=EXAMPLE" --dry-run
```

`langs`, `qualities` veya `download` kullanmadan önce gerekli kullanıcı config dosyasını oluşturun:

```bash
uv run dbdvdl init
```

Aynı işlem için eşdeğer config alt komutunu da kullanabilirsiniz:

```bash
uv run dbdvdl config init
```

Kurulum sırasında farklı bir varsayılan dublaj dili seçmek için:

```bash
uv run dbdvdl init --default-lang tr
```

Varsayılan olarak sadece ses indirmek için:

```bash
uv run dbdvdl init --default-download-mode audio
```

Bu komut şuraya yazar:

```text
~/.config/dubbed-video-downloader/config.yaml
```

İçerik:

```yaml
output_dir: ~/Downloads/dbdvdl-output
ffmpeg_path: ffmpeg
default_lang: en
default_download_mode: video
default_video_quality: best
default_audio_quality: best
retry_on_network_failure: 3
```

`ffmpeg_path: ffmpeg` FFmpeg'i sistem `PATH` içinden bulur. İsterseniz bunun yerine mutlak executable yolu verebilirsiniz.
`default_lang`, `download` komutu `--lang` olmadan çalıştırıldığında kullanılacak dublaj dilidir.
`default_download_mode`, `download` komutu `--mode` olmadan çalıştırıldığında
kullanılacak indirme modudur. Desteklenen değerler `video` ve `audio`.
`default_video_quality`, `--video-quality` verilmediğinde video modundaki
çözünürlük seçimini belirler. Desteklenen değerler `best`, `medium`, `low` veya
`2160p`, `1080p`, `720p` gibi tam çözünürlüklerdir.
`default_audio_quality`, `--audio-quality` verilmediğinde seçilen dublaj ses
akışının kalitesini belirler. Desteklenen değerler `best`, `medium` ve `low`.
`retry_on_network_failure`, geçici metadata, çıkarım ve medya indirme hatalarında
kaç kez yeniden deneneceğini belirler. Network retry davranışını kapatmak için
`0` kullanabilirsiniz.

Config dosyasını görmek veya kaldırmak için:

```bash
uv run dbdvdl config show
uv run dbdvdl config remove
```

Kaldırdıktan sonra yeni config oluşturmak için tekrar `uv run dbdvdl init` çalıştırabilirsiniz.

Birden fazla URL ve opsiyonel çıktı/FFmpeg ayarları verebilirsiniz:

CLI config içindeki `output_dir` altına kaydeder ve `default_lang` değerini
kullanır. Ayrıca `default_download_mode` değerini kullanır. `--output-dir`
verirseniz mutlak yol kullanın; `~` desteklenir. CLI seçenekleri o çalıştırma
için config değerlerini ezer.

```bash
uv run dbdvdl download \
  "https://www.youtube.com/watch?v=EXAMPLE1" \
  "https://www.youtube.com/watch?v=EXAMPLE2" \
  --lang tr \
  --mode video \
  --video-quality 1080p \
  --audio-quality best \
  --output-dir ~/Downloads/dbdvdl-output \
  --ffmpeg-path /path/to/ffmpeg \
  --retry-on-network-failure 5
```

CLI seçenekleri o çalıştırma için config değerlerini ezer; buna
`--mode`, `--video-quality`, `--audio-quality` ve
`--retry-on-network-failure` da dahildir.

Belirli bir URL ve dublaj dili için kullanılabilir kalite seçeneklerini görmek
için `qualities` komutunu kullanabilirsiniz:

```bash
uv run dbdvdl qualities "https://www.youtube.com/watch?v=EXAMPLE" --lang tr
```

Kalite davranışı açık çözünürlüklerde bilinçli olarak katıdır:

- `best`, yt-dlp'nin en iyi eşleşen akışını kullanır.
- Video `medium`, `720p` hedefine en yakın mevcut yüksekliği seçer.
- Video `low`, mevcut en düşük video yüksekliğini seçer.
- `1080p` gibi tam video değerleri tam eşleşme ister; yoksa komut mevcut
  yükseklikleri yazdırarak hata verir.
- Audio `medium`, bitrate metadata'sı varsa seçilen dilde `128k` değerine en
  yakın ses akışını seçer; metadata yoksa not düşerek `best` kullanır.
- Audio `low`, bitrate metadata'sı varsa seçilen dildeki en düşük bitrate'i
  seçer; metadata yoksa not düşerek yt-dlp'nin en kötü eşleşen audio selector'ını
  kullanır.

URL'yi, etkin dublaj dilini, etkin indirme modunu ve kaliteyi doğrulayıp
planlanan çıktı yolunu görmek için `--dry-run` kullanabilirsiniz. Bu mod indirme,
birleştirme veya çıktı klasörü oluşturma işlemi yapmaz:

```bash
uv run dbdvdl download "https://www.youtube.com/watch?v=EXAMPLE" --dry-run
```

CLI çıktısını sade tutmak için yt-dlp ilerleme, bilgi, uyarı ve debug mesajları
varsayılan olarak gizlenir. yt-dlp ilerleme, bilgi ve uyarılarını görmek için
`download` veya `langs` komutlarında `--verbose` kullanabilirsiniz:

```bash
uv run dbdvdl langs "https://www.youtube.com/watch?v=EXAMPLE" --verbose
uv run dbdvdl download "https://www.youtube.com/watch?v=EXAMPLE" --verbose
```

Daha ayrıntılı sorun giderme için `--debug` kullanabilirsiniz. Bu seçenek
yt-dlp debug çıktısını açar ve URL bazlı indirme hatalarında traceback yazdırır:

```bash
uv run dbdvdl langs "https://www.youtube.com/watch?v=EXAMPLE" --debug
uv run dbdvdl download "https://www.youtube.com/watch?v=EXAMPLE" --debug
```

Video modunda araç şu işlemleri yapar:

1. Videoda istenen dublaj dili mevcut mu kontrol eder.
2. Dil yoksa hata verir ve mevcut dillerin listesini gösterir.
3. İstenen video kalitesini ve dublaj ses kalitesini seçer.
4. Videoyu ve seçilen ses parçasını indirir.
5. Bunları `.mkv` dosyasında birleştirir.
6. Dosyayı `<çıktı-klasörü>/<dil>/<kanal>/<başlık>/` klasör yapısına kaydeder.

Ses modunda araç yalnızca seçilen dublajlı ses akışını indirir ve yt-dlp'nin
seçtiği doğal ses uzantısıyla aynı klasör yapısına kaydeder. `--video-quality`
yalnızca video modunda geçerlidir.

`--dry-run` ile araç doğrulama ve çıktı yolu önizlemesinden sonra durur.

## Bağımlılıkları Güncelleme

yt-dlp'yi uv yönetimli proje içinde güncellemek için:

```bash
uv lock --upgrade-package yt-dlp
uv lock --upgrade-package yt-dlp-ejs
uv sync
```

Bağımlılık sürümleri değiştiğinde güncellenen `uv.lock` dosyasını commit edin. `uv.lock` dosyasını elle düzenlemeyin.

## Notlar

- YouTube çıkarımı başarısız olursa veya beklenmedik davranırsa, yt-dlp ilerleme ve uyarılarını görmek için aynı `langs` veya `download` komutunu `--verbose` ile, debug logları ve traceback için `--debug` ile tekrar çalıştırın.
- Çıktı klasörünü değiştirmek için `--output-dir` kullanabilirsiniz.

## Yasal Uyarı

- Bu araç yalnızca **kişisel ve eğitim amaçlı kullanım** için sağlanmaktadır.
- YouTube'un [Kullanım Şartları](https://www.youtube.com/static?template=terms) ve içerik üreticilerin haklarına saygı gösterin.
- İzin alınmadan video indirip yeniden paylaşmak telif haklarını ihlal edebilir.

## Anahtar Kelimeler

*YouTube video indirme, YouTube dublaj indirici, çok dilli ses, yt-dlp, ffmpeg, mkv, YouTube dublajlı video indirme, YouTube dublajlı video indir, Python YouTube downloader*
