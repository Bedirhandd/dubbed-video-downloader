# YouTube Dublajlı Video İndirici

YouTube videolarını veya seslerini **istediğiniz dublaj diliyle** indirin - Japonca, Fransızca, Portekizce ve daha fazlası.

Yapay zeka, içerik üreticilerinin aynı videoyu birden fazla dilde dublajlı sesle yayınlamasını her zamankinden kolaylaştırdı. Eskiden tek dilde yayınlayan kanallar artık çoğu zaman Almanca, Hintçe, Korece ve daha fazlasını tek bir yüklemede sunuyor.

YouTube'da başka bir dublaja geçmek birkaç tıklama. YouTube dışında istediğiniz parçayı almak başka bir hikaye. Çoğu indirici varsayılan akışı alır, alternatif dilleri format dizelerinin arkasına gizler ya da dosyaları size hiçbir şey anlatmayan isimlerle kaydeder.

Peki Fransızca dublajlı videoyu nasıl indireceksiniz, ya da yalnızca Japonca sesi nasıl kaydedeceksiniz? Bu CLI tam bunun için: dublaj parçasını bulur, kaliteyi seçer ve sonucu öngörülebilir bir yere kaydeder.

> İngilizce özet için [README.md](README.md) dosyasına bakın. Ayrıntılı dokümantasyon [docs/](docs/index.md) klasöründedir (İngilizce).

## Neden var?

Bu araç [yt-dlp](https://github.com/yt-dlp/yt-dlp) ve [FFmpeg](https://ffmpeg.org/) üzerine küçük, amaca yönelik bir iş akışı kurar:

- **Dil öncelikli** - indirmeye başlamadan önce mevcut dublajları listeler.
- **Düzenli çıktı** - dosyalar `dil / kanal / başlık` altına gider; İndirilenler klasöründe rastgele bir dosya adıyla kalmaz.
- **Video veya ses** - dublajlı sesi `.mkv` içinde birleştirir ya da yalnızca ses akışını kaydeder.
- **Mantıklı varsayılanlar** - kısa bir kurulum adımı tercihlerinizi saklar; gerektiğinde her çalıştırmada geçersiz kılabilirsiniz.
- **Çökme güvenli staging** - indirmeler önce geçici bir staging alanına gider; yarım kalan çalışmalar otomatik temizlenir ve sonlandırma atomiktir; yarım yazılmış dosyalar kütüphanenize karışmaz.

## Hızlı başlangıç

**Platform:** Şimdilik yalnızca Linux. Windows ve macOS henüz desteklenmemektedir.

```bash
pipx install dubbed-video-downloader   # önerilen
# pip install dubbed-video-downloader  # alternatif
dbdvdl init
dbdvdl doctor
dbdvdl download "https://www.youtube.com/watch?v=VIDEO_ID"
```

Katkıda bulunuyorsanız [kaynak koddan kurulum](docs/getting-started/installation.md#install-from-source) için uv kullanın.

Ön koşullar, ilk indirme adımları ve sorun giderme için [Hızlı Başlangıç](docs/getting-started/quickstart.md) bölümüne bakın.

## Dokümantasyon

Tüm dokümantasyon [docs/](docs/index.md) klasöründedir:

| Bölüm | İçerik |
| --- | --- |
| [Başlarken](docs/getting-started/installation.md) | [Kurulum](docs/getting-started/installation.md), [bağımlılıklar](docs/getting-started/dependencies.md), [hızlı başlangıç](docs/getting-started/quickstart.md) |
| [Komutlar](docs/commands/overview.md) | [init](docs/commands/init.md), [doctor](docs/commands/doctor.md), [langs](docs/commands/langs.md), [qualities](docs/commands/qualities.md), [download](docs/commands/download.md), [config](docs/commands/config.md) |
| [Yapılandırma](docs/configuration/overview.md) | [Config anahtarları](docs/configuration/config-keys.md), [yönetim](docs/configuration/management.md) |
| [Kullanım örnekleri](docs/usage-examples/index.md) | İndirme, dil, kalite, betikleme ve [sorun giderme](docs/usage-examples/troubleshooting.md) |
| [Özellikler](docs/features/language-resolution.md) | [Dil çözümleme](docs/features/language-resolution.md), [kalite](docs/features/quality-selection.md), [indirme modları](docs/features/download-modes.md), [çıktı düzeni](docs/features/output-layout.md), [aşamalı indirme](docs/features/staged-downloads.md) |
| [SSS](docs/faq/general.md) | [Kurulum](docs/faq/installation-and-setup.md), [diller](docs/faq/language-and-dubs.md), [indirmeler](docs/faq/quality-and-downloads.md), [sorun giderme](docs/faq/troubleshooting.md) |
| [Mimari](docs/architecture/overview.md) | Katkıda bulunanlar için: [modüller](docs/architecture/modules.md), [indirme hattı](docs/architecture/download-pipeline.md), [testler](docs/architecture/testing.md) |

## Yakında

- **Toplu indirme** - oynatma listelerini, kanalları veya URL listelerini ortak varsayılanlarla kuyruğa alma
- **Çıktı formatı özelleştirme** - mevcut varsayılanların ötesinde konteyner ve adlandırma seçimi
- **GUI** - bayrakları ezberlemeden aynı iş akışı için masaüstü arayüzü
- **Windows uyumluluğu** - Windows'ta daha sorunsuz ilk kurulum ve paketleme

## Sorun bildirin

Bir hata veya beklenmeyen davranış mı gördünüz? GitHub'da [issue açın](https://github.com/Bedirhandd/dubbed-video-downloader/issues). Önce [sorun giderme rehberi](docs/usage-examples/troubleshooting.md) ve [SSS](docs/faq/troubleshooting.md) yardımcı olabilir.

## Katkıda bulunma

Pull request'ler memnuniyetle karşılanır. [CONTRIBUTING.md](CONTRIBUTING.md) ve [geliştirme SSS](docs/faq/usage-and-development.md) bölümüne bakın.

## Yasal uyarı

Bu araç yalnızca **eğitim ve kişisel kullanım** için sağlanmaktadır. [YouTube Kullanım Şartları](https://www.youtube.com/static?template=terms)'na ve içerik üreticilerinin haklarına saygı gösterin. İzinsiz video indirmek ve yeniden paylaşmak telif haklarını ihlal edebilir.

## Lisans

Bu proje [MIT License](LICENSE) altında lisanslanmıştır.
