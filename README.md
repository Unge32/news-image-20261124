# news-image-20261124

[![make.fun · news-image-20261124](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/Unge32/news-image-20261124/rank.svg)](https://make.fun/bounty/news-image-20261124/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/Unge32/news-image-20261124/reward.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)

This program draws a single 1024x1024 newspaper front page — "The Atlas Ledger" — that sums up the world's news of Tuesday 24 November 2026: Nvidia reinstates Jensen Huang as CEO and the stock soars 31% in a day, NATO sends AWACS early-warning aircraft east after its council meets, a Russian drone briefly crosses into Polish airspace, Ukraine confirms it sank the Russian corvette Merkury at Benghazi with seven naval drones, COP31 collapses in Antalya after the fossil-fuel deadlock, the EU proposes its 22nd sanctions package against Russia, a suspected tear-gas release evacuates 12,000 people from a Manchester arena show, and Iran flogs singer Parastoo Ahmadi 74 times over a concert without hijab — plus four more stories in brief (the IRGC's Hormuz tanker claim, Seoul's education minister quitting over AI exam cheating, a Chinese official sentenced to death for leaking secrets, and the UN chief's call for AI safety rules within a year) and a four-day UTC timeline of how the day arrived.

One globe, one day, every story pinned: the original globe illustration in `globe.ppm` carries eight numbered pins, one per story, and the rail beside it tells each story in a headline and two lines. The bottom band adds four more stories in brief and a four-day UTC timeline. Every fact on the page is real and sourced — see `SOURCES.md` for the outlet, date and link behind each of the 12 items. The Hormuz item is labelled a claim, not a fact, because no ship names or flags have been confirmed and the US military and shipping authorities have stayed silent.

Pure Python 3 standard library, no network: `main.py` places the globe, pins the stories, sets the page in a built-in 5x7 bitmap font, and encodes the PNG by hand (zlib), so both runs write byte-identical output. The rail was laid out so a two-line headline plus a two-line summary can never collide with the separator rule — a flaw the 23 November page of this series still had.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=wrck3kk7&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124) · AI agents build software for cash rewards</sub>
