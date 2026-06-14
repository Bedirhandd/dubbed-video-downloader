# YouTube Dublajlı Video İndirici

YouTube videolarını veya seslerini **istediğiniz dublaj diliyle** indirin - Japonca, Fransızca, Portekizce ve daha fazlası.

Yapay zeka, içerik üreticilerinin aynı videoyu birden fazla dilde dublajlı sesle yayınlamasını her zamankinden kolaylaştırdı. Eskiden tek dilde yayınlayan kanallar artık çoğu zaman Almanca, Hintçe, Korece ve daha fazlasını tek bir yüklemede sunuyor.

YouTube'da başka bir dublaja geçmek birkaç tıklama. YouTube dışında istediğiniz parçayı almak başka bir hikaye. Çoğu indirici varsayılan akışı alır, alternatif dilleri format dizelerinin arkasına gizler ya da dosyaları size hiçbir şey anlatmayan isimlerle kaydeder.

Peki Fransızca dublajlı videoyu nasıl indireceksiniz, ya da yalnızca Japonca sesi nasıl kaydedeceksiniz? Bu CLI tam bunun için: dublaj parçasını bulur, kaliteyi seçer ve sonucu öngörülebilir bir yere kaydeder.

> İngilizce dokümantasyon için [README.md](README.md) dosyasına bakın.

## Neden var?

Bu araç [yt-dlp](https://github.com/yt-dlp/yt-dlp) ve [FFmpeg](https://ffmpeg.org/) üzerine küçük, amaca yönelik bir iş akışı kurar:

- **Dil öncelikli** - indirmeye başlamadan önce mevcut dublajları listeler.
- **Düzenli çıktı** - dosyalar `dil / kanal / başlık` altına gider; İndirilenler klasöründe rastgele bir dosya adıyla kalmaz.
- **Video veya ses** - dublajlı sesi `.mkv` içinde birleştirir ya da yalnızca ses akışını kaydeder.
- **Mantıklı varsayılanlar** - kısa bir kurulum adımı tercihlerinizi saklar; gerektiğinde her çalıştırmada geçersiz kılabilirsiniz.

Perde arkasında indirmeler önce geçici bir klasöre alınır ve yalnızca tamamlandığında asıl konuma taşınır. Yarıda kesilen çalışmalar kendini temizler. Diske bir şey yazılmadan önce `--dry-run` ile indirmeyi önizleyebilirsiniz.

## Hızlı başlangıç

**Gereksinimler:** [uv](https://docs.astral.sh/uv/), Python 3.10+, [Node.js](https://nodejs.org/) (YouTube JS çözücüsü için) ve `PATH` üzerinde **FFmpeg**.

**Platform:** Bu proje şu an Linux üzerinde geliştirilmekte ve test edilmektedir. Windows ve macOS henüz desteklenmemektedir ve büyük ihtimalle beklendiği gibi çalışmaz.

```bash
git clone https://github.com/Bedirhandd/dubbed-video-downloader.git
cd dubbed-video-downloader
uv sync
uv run dbdvdl init
uv run dbdvdl doctor
```

`doctor`, Python'u, config dosyanızı, FFmpeg'i, Node.js'i ve sabitlenmiş yt-dlp paketlerini kontrol eder - her şeyin hazır olduğunu doğrulamanın hızlı yolu.

**İlk indirme:**

```bash
# Videonun hangi dublaj dillerini sunduğunu görün
uv run dbdvdl langs "https://www.youtube.com/watch?v=VIDEO_ID"

# Varsayılan dilinizle indirin (init sırasında ayarlanır)
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID"

# Ya da dili ve kaliteyi açıkça seçin
uv run dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID" --lang ko --video-quality 1080p
```

Tüm komut listesi için `uv run dbdvdl --help` çalıştırın.

## Komutlar

| Komut | Ne yapar |
| --- | --- |
| `init` | Varsayılanlarınızla `~/.config/dubbed-video-downloader/config.yaml` oluşturur |
| `doctor` | Python, config, FFmpeg, Node.js ve bağımlılıkları doğrular |
| `langs URL` | Bir video için kullanılabilir dublaj dillerini listeler |
| `qualities URL` | Bir dil için video ve ses kalite seçeneklerini gösterir |
| `download URL…` | Bir veya daha fazla video indirir |
| `config show` | Geçerli yapılandırmanızı yazdırır |
| `config remove` | Config dosyasını kaldırır |

`download` üzerinde kullanışlı bayraklar: `--lang`, `--mode video|audio`, `--video-quality`, `--audio-quality`, `--dry-run`, `--if-exists skip|fail|overwrite`, `--verbose`, `--debug`.

## Dosyalar nereye gider?

Video indirmeleri `.mkv` olarak kaydedilir:

```text
~/Downloads/dbdvdl-output/es/<channel>/<title>/<title>.mkv
```

Yalnızca ses indirmeleri aynı klasör düzenini kullanır ve doğal uzantıyı korur (`.webm`, `.m4a` vb.).

İndirme sırasında kısmi dosyalar, işlem başarıyla bitene kadar `<output-dir>/tmp/.incomplete/` altında kalır.

## Yapılandırma

`dbdvdl init`, `~/.config/dubbed-video-downloader/config.yaml` dosyasına bir YAML config yazar. Çıktı klasörü, dublaj dili, indirme modu, kalite ön ayarları, ağ yeniden denemeleri ve mevcut dosyaların nasıl ele alınacağı için varsayılanlar belirleyebilirsiniz.

```bash
uv run dbdvdl init --default-lang de
uv run dbdvdl config show
```

CLI bayrakları tek bir çalıştırma için config değerlerini geçersiz kılar. Tüm anahtarların ve davranışın tam listesi için `uv run dbdvdl init --help` çalıştırın ya da oluşturulmuş config'i `config show` ile inceleyin.

## Yakında

- **Toplu indirme** - oynatma listelerini, kanalları veya URL listelerini ortak varsayılanlarla kuyruğa alma
- **Çıktı formatı özelleştirme** - mevcut varsayılanların ötesinde konteyner ve adlandırma seçimi
- **GUI** - bayrakları ezberlemeden aynı iş akışı için masaüstü arayüzü
- **Windows uyumluluğu** - Windows'ta daha sorunsuz ilk kurulum ve paketleme

## Sorun bildirin

Bir hata, çökme veya dokümantasyonla uyuşmayan bir davranış mı buldunuz? GitHub'da [issue açın](https://github.com/Bedirhandd/dubbed-video-downloader/issues).

Yardımcı olacak bilgiler:

- Çalıştırdığınız komut
- Beklediğiniz sonuç ile gerçekte olan
- İşletim sisteminiz ve Python sürümünüz (`dbdvdl doctor` çıktısı burada işe yarar)
- Sorun tekrar üretmekte zorsa `--verbose` veya `--debug` çıktısı

Öneri ve özellik fikirleri de memnuniyetle karşılanır - [yakında](#yakında) listesinde olsun ya da olmasın.

## Katkıda bulunma

Pull request'ler memnuniyetle karşılanır. Dal adlandırma, commit stili ve test paketini yerelde çalıştırma için [CONTRIBUTING.md](CONTRIBUTING.md) dosyasına bakın.

## Yasal uyarı

Bu araç yalnızca **eğitim ve kişisel kullanım** için sağlanmaktadır. [YouTube Kullanım Şartları](https://www.youtube.com/static?template=terms)'na ve içerik üreticilerinin haklarına saygı gösterin. İzinsiz video indirmek ve yeniden paylaşmak telif haklarını ihlal edebilir.

## Lisans

Bu proje [MIT License](LICENSE) altında lisanslanmıştır.
