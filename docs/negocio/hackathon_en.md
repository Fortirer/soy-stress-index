# Precision & Digital Agriculture Hackathon, UIUC (issue #22)

- **When:** 13–15 November 2026, in person
- **Where:** John Deere Technology Innovation Center, 2021 S 1st St, Ste 101, Champaign
- **Apply by:** 6 November (aim for 30 October): [registration form](https://illinois.qualtrics.com/jfe/form/SV_1MvID9obnEipBiu)
- **Rules:** students, researchers, professionals and startups can enter. Teams have up to 4 people; solo participants are welcome and get matched to a team.
- **Format:** the challenges are announced at kickoff on 13 November, in four tracks (plant and controlled environment; livestock; automation and robotics; food, supply chain and agricultural systems). Each team picks one challenge, first come first served. There are prizes per challenge and per track.
- **Fee:** none listed. Ask.
- Source: [Center for Digital Agriculture](https://digitalag.illinois.edu/precision-digital-agriculture-hackathon/)

**What this changes in the issue:** the challenges are only announced at kickoff, so the "stress-map demo" may not fit any of them. Treat the hackathon mainly as a place to **meet a cofounder (#18), mentors and judges**, and enter whichever challenge fits best: likely *Plant & Controlled Environment Systems* or *Food, Supply Chain & Agricultural Systems*. Check the rules before bringing the Turgor index as existing work; most hackathons only allow open-source code written before the event, which this repository is.

## Email to digitalag@illinois.edu (send now)

> **Subject:** Hackathon 13–15 Nov: a few questions from a visiting researcher
>
> Dear CDA team,
>
> I am a visiting PhD researcher from the University of São Paulo, currently at the University of Illinois, working on soybean drought and heat stress from satellite and weather data. I plan to apply to the Precision & Digital Agriculture Hackathon and have three quick questions:
>
> 1. Is there a registration fee?
> 2. What time does kickoff start on 13 November, and do participants need to stay on site overnight?
> 3. May participants use open-source code and public datasets they developed before the event (for example, an open soybean stress index on GitHub), as long as the hackathon work itself is new?
>
> I am applying solo and would be glad to join a team.
>
> Thank you,
> Janaina Fortirer
> psjana@usp.br

## Application answers (draft)

The form fields are not public. Adapt these to whatever it asks.

- **Background:** plant ecophysiologist, PhD candidate at the University of São Paulo (Brazil), visiting researcher at the University of Illinois. I study soybean under elevated CO2, drought and warming, from gas exchange to gene expression. I also build satellite and weather pipelines in Python (Sentinel-2, MODIS, NASA POWER) and R.
- **What I bring to a team:** crop physiology (what stress does at each growth stage), remote-sensing time series, model validation (backtests, confidence intervals), and an open soybean stress index validated on 780 Brazilian municipalities over 2001–2025.
- **What I want from the event:** build something useful with people from engineering and data science, meet potential collaborators for an agtech startup on climate risk for crop lenders and insurers, and get feedback from industry mentors.
- **Preferred track:** Plant & Controlled Environment Systems; also happy with Food, Supply Chain & Agricultural Systems.
- **Team:** solo, open to being matched.

## Plan for the weekend

**Before (by 12 Nov)**

- Print 20 copies of the one-pager (#23) and the cofounder page ([`cofounders_en.md`](cofounders_en.md)).
- Practise the 3-minute pitch (#23).
- Put the laptop demo ready: the monitor replay of 15 Feb 2025 (`monitor/replays/2024-25/2025-02-15/map.png`) and the validation report (EN).

**Build at the event (if the challenge fits)**

- A clickable map of RS and PR with the week-by-week replay of the 2021/22 drought (`scripts/17_monitor.py --asof` for each Monday, December to April).
- Field view: Sentinel-2 curves for a few fields (fig. 5).

**People**

- For each judge or mentor from industry (John Deere, insurers, lenders), ask the interview questions: how do you find out about crop losses today, and what does it cost?
- Log each contact (name, organisation, what they said, next step) in the interview tracker, as a new target if they fit.
- Follow up within 48 hours.
