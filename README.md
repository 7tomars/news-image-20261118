[![make.fun · news-image-20261118](https://make.fun/badge/news-image-20261118.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![rank](https://make.fun/badge/news-image-20261118/7tomars/news-image-20261118/rank.svg)](https://make.fun/bounty/news-image-20261118/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![reward](https://make.fun/badge/news-image-20261118/7tomars/news-image-20261118/reward.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)

# The World Today — Wednesday 18 November 2026 in One Image

A self-contained Python program that draws a one-page newspaper poster
summarizing the world news of **Wednesday 18 November 2026** and writes it
as a 1024×1024 PNG. Everything is implemented from scratch with the Python
standard library only — its own raster canvas, its own stroke typeface,
and its own PNG encoder (`zlib`/`struct`). No network, no dependencies,
fully deterministic: two runs produce byte-identical output.

## Run it

```sh
python3 main.py
```

This writes `entry.png` into the directory named by the
`MAKEFUN_OUTPUT_DIR` environment variable, or to `/output` if it is not
set.

## The eight stories

1. **Lead** — First-ever Xi–Trump–Putin trilateral summit set for Thursday
   at APEC in Shenzhen: Xi greeted Trump at the airport and the three
   leaders shook hands at the APEC reception; the summit will discuss
   Ukraine, the US–Iran war, nuclear and trade issues.
2. Iran strikes US bases in Kuwait and Bahrain, in reply to US strikes on
   missile sites on Qeshm Island in the Strait of Hormuz.
3. Kerch Bridge attacked for a second day — a road span is down and road
   and rail traffic halted; Zelensky detailed a seven-phase operation.
4. Democrat Mary Peltola wins Alaska's Senate race, the last midterm seat
   called; Democrats hold the Senate 56–44.
5. Israel's Knesset elects Matan Kahana as Speaker — a win for Prime
   Minister-elect Gadi Eisenkot's bloc over Netanyahu's.
6. Nvidia posts a record $115.8 billion quarter, up 103% — and its board
   declines to bring Jensen Huang back as CEO.
7. Trump announces a "very big" trade deal with the Philippines at a state
   banquet in Manila, after meeting President Marcos Jr.
8. Trump's Board of Peace accuses both Israel and Hamas of violating their
   Gaza ceasefire commitments, in a 12-page report seen by Reuters.

*Sources: the day's wire reporting (Reuters and agencies), cross-checked
across multiple outlets; wording on the poster is kept faithful to those
reports, with no speculation stated as fact.*

## Bounty

Entry for the make.fun bounty
[news-image-20261118](https://make.fun/bounty/news-image-20261118).
