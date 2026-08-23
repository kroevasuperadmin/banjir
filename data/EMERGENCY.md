# Malaysia flood emergency contacts + checklist (verified 23 Aug 2026)

Every number below was read from an official .gov.my page/PDF on 23 Aug 2026. "Verified from" = the page we actually opened. Nothing here is inferred.

## Emergency numbers (national)

- **999** — MERS 999, single national emergency number (police PDRM, Bomba JBPM, ambulance KKM, Civil Defence APM). Free. Since 1 Oct 2007 it merges the old 991 and 994 lines.
  Verified from: APM, https://www.civildefence.gov.my/perkhidmatan-kecemasan-999/
- **991** — Talian Kecemasan 991, Angkatan Pertahanan Awam (APM / Civil Defence). Free; still answered, routed into MERS 999.
  Verified from: same APM page as above.
- **994** — Jabatan Bomba dan Penyelamat (fire & rescue). Merged into 999 per APM page; still the Bomba number in public use. **bomba.gov.my was unreachable (connection refused) from the venue AND from a remote fetch on 23 Aug** — 994 is cited via the APM page, not Bomba's own site.
- **03-8064 2400 / 03-8064 2429** — NADMA National Disaster Command Centre (NDCC / Pusat Kawalan Bencana Negara), 24 h. Email opsroom@nadma.gov.my.
  Verified from: NADMA Portal Bencana, https://portalbencana.nadma.gov.my/en/component/sppagebuilder/?view=page&id=4493 (state-level PKOB list on the same page).
- **15999** — Talian Kasih (JKM / KPWKM), 24 h; covers disaster victims (mangsa bencana) + welfare. WhatsApp 019-261 5999.
  Verified from: KPWKM https://www.kpwkm.gov.my/portal-main/article?id=talian-kasih ; MyGov https://www.malaysia.gov.my/en/categories/law--safety/vulnerable-groups/talian-kasih-15999 . **jkm.gov.my unreachable from venue and remote** — cited via KPWKM/MyGov, not JKM's own site.
- **+603-8920 6000** — APM HQ (Kajang). Verified from: https://www.civildefence.gov.my/hotline-apm/

## State hotlines

### APM Hotline 24 jam (Civil Defence, per state)
Verified from: https://www.civildefence.gov.my/hotline-apm/ (page updated 21 Aug 2026)
- **WP Kuala Lumpur:** 03-2687 1400
- **Selangor:** 03-3371 0820
- **Perlis:** 04-977 7991 / 04-977 8991
- **Kedah:** 04-732 3810 / 04-732 3801
- **Pulau Pinang:** 04-226 3876
- **Perak:** 05-527 8715
- **Pahang:** 09-544 5991
- **Terengganu:** 09-666 8246 / 09-667 2991
- **Kelantan:** 09-747 4091
- **Negeri Sembilan:** 06-764 5755
- **Melaka:** 06-232 4028
- **Johor:** 07-234 9706 / 07-234 9708 / 07-234 9709
- **Sabah:** 088-232 440 / 088-232 453
- **Sarawak:** 082-433 896 / 082-370 205

### PKOB — Pusat Kawalan Operasi Bencana (state disaster ops centres, NADMA list)
Verified from: https://portalbencana.nadma.gov.my/images/ndcc/documents/PKOB/SENARAI_NOMBOR_PEJABAT_DAERAH.pdf (4 pages, district-level numbers inside)
- **Kuala Lumpur:** 03-2617 9059
- **Putrajaya:** 03-8887 7999
- **Labuan:** 087-408 776
- **Selangor:** 03-5650 0502 / 03-5650 0506 (Gombak 03-6126 1482, Petaling 03-7841 9462)
- **Perlis:** 04-976 0991
- **Kedah (Sekretariat APM):** 04-702 9393 / 04-702 9394
- **Pulau Pinang:** 04-262 1819 / 04-262 1207
- **Perak:** 05-209 5013
- **Negeri Sembilan:** 06-761 3461
- **Melaka:** 06-230 7624 / 06-232 7467
- **Johor:** 07-232 2484 / 07-232 2485
- **Pahang:** 09-512 4567 / 4532 / 4553
- **Kelantan:** 09-748 1180
- **Terengganu:** 09-623 6655 / 09-623 6644
- **Sabah:** 088-369 403
- **Sarawak:** 082-443 991

## Where to get live info (official)
- Flood warnings / river levels: JPS Public InfoBanjir — https://publicinfobanjir.water.gov.my (our `data/jps.py`)
- Weather warnings: MET Malaysia — https://www.met.gov.my / data.gov.my API (our `data/met.py`)
- Open relief centres (PPS) + evacuee counts: JKM InfoBencana — https://infobencanajkmv2.jkm.gov.my/landing/ (our `data/pps.py`). NADMA's portal links this as the official PPS dashboard.
- Road closures: JKR — https://bencana.jkr.gov.my/ (**unreachable from venue, 000 — not integrated**)
- NADMA Portal Bencana (hub): https://portalbencana.nadma.gov.my/ (**403 from venue wifi; reachable remotely**)

## Flood checklist — NADMA official (transcribed from NADMA infographics, BM → EN)
Source images (NADMA / Jabatan Perdana Menteri):
- Before: https://portalbencana.nadma.gov.my/images/2024/11/07/persediaan-sebelum-banjir.png
- During: https://portalbencana.nadma.gov.my/images/2024/11/07/persediaan-semasa-banjir.png
- After: https://portalbencana.nadma.gov.my/images/2024/11/07/persediaan-selepas-banjir.png
- Emergency bag (Monsun Timur Laut 2025/2026): https://portalbencana.nadma.gov.my/images/ndcc/documents/infografik/Beg_Kecemasan_MTL.jpg

**Persediaan Sebelum Banjir (before):**
- Peka terhadap amaran banjir — stay alert to flood warnings
- Sediakan beg kecemasan — prepare an emergency bag
- Simpan dokumen penting dalam bekas kalis air — keep important documents in a waterproof container
- Berpindah sekiranya diarahkan pihak berkuasa — evacuate when instructed by the authorities

**Langkah-Langkah Semasa Banjir (during):**
- Dapatkan maklumat situasi terkini dari sumber yang sahih — get updates from official sources only: weather = Jabatan Meteorologi Malaysia, flood = Jabatan Pengairan dan Saliran Malaysia
- Berpindah segera apabila diarahkan — evacuate immediately when told
- Jangan sentuh sebarang peranti elektrik dalam keadaan basah — don't touch electrical devices while wet
- Jangan cuba harungi banjir — never attempt to wade/drive through floodwater

**Langkah-Langkah Selepas Banjir (after):**
- Elakkan kawasan kabel elektrik yang terputus — avoid areas with downed power cables
- Segera berjumpa doktor jika terkena sebarang penyakit — see a doctor immediately if you fall ill
- Elakkan memakan makanan yang terkena air banjir — don't eat food touched by floodwater
- Pulang ke rumah setelah situasi disahkan selamat — return home only once declared safe

**Beg Kecemasan — suggested contents (NADMA MTL 2025/2026):**
- Air bersih (clean water) · Makanan tahan lama (non-perishable food) · Wang (cash) · Wisel (whistle)
- Radio mini mudah alih berbateri (battery radio) · Telefon & pembekal kuasa mudah alih (phone + power bank)
- Lampu suluh & bateri (torch + batteries) · Kit kecemasan & ubat-ubatan (first-aid kit + medicines)
- Pakaian (clothes) · Dokumen penting (important documents)

## Unreachable on 23 Aug 2026 (note, don't retry in a loop)
- `infobencanajkm.jkm.gov.my` (old v1 host) — 000 http + https. Superseded by `infobencanajkmv2.jkm.gov.my` (works).
- `myinfobencana.nadma.gov.my` — 000.
- `www.jkm.gov.my` — 000 from venue; ECONNREFUSED remotely.
- `www.bomba.gov.my` — 000 from venue; ECONNREFUSED remotely.
- `bencana.jkr.gov.my` — 000 from venue.
- `portalbencana.nadma.gov.my` HTML pages — 403 from venue (PDF/image assets on the same host DO load); fine remotely.
- `www.malaysia.gov.my` — curl segfault (TLS) from venue.
- `infobencanajkmv2.jkm.gov.my/api/data-dashboard-table-pps.php` — returns `null` unless you pass `seasonmain_id` scraped from /landing/ (currently 221); gives opened-date, capacity, gender/age breakdown. Not used — `pusat-buka.php` is stateless and enough.
