---
trigger: always_on
---

# Universal Skill-Aware Agent Instructions — BankMate

## Skill Location
Barcha skill papkalari shu yerda joylashgan:
`C:\Users\User\001_AI_Proyektlar\BankMate\.agents\skills`

Har bir papkada `SKILL.md` fayli bor. Vazifa boshlanishidan oldin shu papkani skan qil.

## Core Principle
Har bir topshiriqda, men aytmasam ham, avtomatik mos skillni tanlab ishlat. Ruxsat so'rama, jarayonni tushuntirma — jim analiz qilib, to'g'ridan-to'g'ri bajar.

## Mandatory First Step
Vazifani bajarishdan OLDIN: `.agents\skills` ichidagi papkalarni ko'rib chiq, mos keladigan(lar)ning SKILL.md faylini o'qi. Bir nechta skill mos kelishi mumkin — barchasini ishlat. Faqat birini o'qib to'xtama.

## Skill Routing Map

**Backend / Python:**
- `python-pro` — umumiy Python kodi, refactoring, best practices
- `fastapi` — FastAPI endpoint, router, dependency, async API
- `pydantic-ai` — Pydantic AI agent / LLM integratsiya
- `pydantic-models-py` — Pydantic model, validatsiya, schema

**Database / SQL:**
- `sql-pro` — SQL query yozish, schema dizayn
- `sql-optimization-patterns` — sekin query, indeks, query plan optimizatsiya
- `alembic` — DB migration yaratish va boshqarish

**Frontend / React / Next.js:**
- `react-hooks` — React hook (useState/useEffect/custom)
- `next-js-16-launchpad` — Next.js 16 setup va arxitektura
- `next-cache-components-optimizer` — Next.js cache va komponent optimizatsiya
- `next-dev-loop` — Next.js dev workflow, debugging
- `shadcn-ui` — shadcn/ui komponentlari bilan UI
- `zustand` — Zustand state management
- `fullstack-developer` — to'liq fullstack feature (frontend+backend birga)

**Security / Testing:**
- `sql-injection-testing` — SQL injection zaifligini test qilish
- `sqlmap-database-pentesting` — sqlmap bilan DB pentesting

**Career:**
- `discovery-interview-prep` — texnik intervyuga tayyorgarlik

## Routing Qoidalari
- Yangi API endpoint? → `fastapi` (+ kerak bo'lsa `pydantic-models-py`)
- Sekin DB query? → `sql-optimization-patterns` (+ `sql-pro`)
- DB strukturasi o'zgaradimi? → `alembic` migration
- React UI komponent? → `shadcn-ui` + `react-hooks` (state bo'lsa `zustand`)
- Next.js sahifa/proyekt? → `next-js-16-launchpad` (optimizatsiya: `next-cache-components-optimizer`)
- To'liq feature (UI+API+DB)? → `fullstack-developer` + tegishli sub-skilllar
- Xavfsizlik testi? → `sql-injection-testing` / `sqlmap-database-pentesting`

## Hard Rules
1. Kod yozish yoki run qilishdan OLDIN tegishli SKILL.md ni o'qi — majburiy.
2. "Bilaman" deb skillni o'qimaslik mumkin emas — skilllar muhit-spetsifik cheklovlarni saqlaydi.
3. Skill tanlashni "kerakmi" deb avval hal qilma — vazifaga mos kelsa, o'qi.
4. Silent execution: skill o'qiganingni aytma, natijani ber.

## Output
Tayyor, foydalanishga shay natijalar ber — ortiqcha tushuntirishsiz.
