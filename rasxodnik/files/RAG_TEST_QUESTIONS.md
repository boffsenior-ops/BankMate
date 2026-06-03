# BankMate — RAG Test savollar to'plami (Ground Truth)

> STEP 4 (RAG pipeline) ni sinash uchun. Har bir savolni `rag_spike.py` yoki chat orqali bering va AI javobini bu yerdagi to'g'ri javob bilan solishtiring.
>
> Barcha javoblar test hujjatlardagi SOXTA ma'lumotlarga asoslangan.

---

## 📄 01_ipoteka_krediti.pdf bo'yicha savollar

| # | Savol | To'g'ri javob | Manba |
|---|-------|---------------|-------|
| 1 | Ipoteka krediti foiz stavkasi qancha? | 18% (yillik) | TEST-KR-001, 2-bo'lim |
| 2 | Ipoteka uchun minimal boshlang'ich to'lov qancha? | 25% | TEST-KR-001, 2-bo'lim |
| 3 | Ipoteka krediti maksimal muddati necha yil? | 20 yil | TEST-KR-001, 2-bo'lim |
| 4 | Ipoteka uchun qarz oluvchining yoshi qancha bo'lishi kerak? | 21 yoshdan 65 yoshgacha | TEST-KR-001, 3-bo'lim |
| 5 | Kredit arizasi necha kunda ko'rib chiqiladi? | 5 ish kuni (murakkab holatda 10 gacha) | TEST-KR-001, 5-bo'lim |
| 6 | Ipotekani erta to'lashda jarima bormi? | Yo'q, hech qanday jarima yoki komissiya yo'q | TEST-KR-001, 6-bo'lim |

## 📄 02_aml_kyc_protsedura.pdf bo'yicha savollar

| # | Savol | To'g'ri javob | Manba |
|---|-------|---------------|-------|
| 7 | KYC qaysi summadan boshlab majburiy? | 15 000 000 so'mdan yuqori operatsiyada | TEST-CM-002, 2-bo'lim |
| 8 | PEP nima va u bilan qanday ishlanadi? | Siyosiy ta'sirga ega shaxs; filial boshlig'i ruxsati, mablag' manbai aniqlanadi, 6 oyda qayta tekshiruv | TEST-CM-002, 3-bo'lim |
| 9 | Shubhali operatsiya necha soatda xabar qilinadi? | 24 soat ichida Compliance bo'limiga | TEST-CM-002, 4-bo'lim |
| 10 | Identifikatsiya hujjatlari qancha saqlanadi? | Kamida 5 yil | TEST-CM-002, 5-bo'lim |
| 11 | Yuridik shaxs uchun qanday hujjatlar kerak? | Ustav, ro'yxatdan o'tish guvohnomasi, rahbar pasporti | TEST-CM-002, 2-bo'lim |

## 📄 03_plastik_karta.pdf bo'yicha savollar

| # | Savol | To'g'ri javob | Manba |
|---|-------|---------------|-------|
| 12 | Visa Gold kartaning yillik xizmat haqi qancha? | 350 000 so'm | TEST-KT-003, 1-bo'lim |
| 13 | Karta necha kunda tayyorlanadi? | 3-5 ish kuni | TEST-KT-003, 2-bo'lim |
| 14 | Kartani qanday bloklash mumkin? | Call-markaz 1234, mobil ilova, yoki filialga murojaat | TEST-KT-003, 3-bo'lim |
| 15 | Bankomatdan kunlik naqd pul limiti qancha? | 20 000 000 so'm | TEST-KT-003, 4-bo'lim |
| 16 | Kartani qayta chiqarish qancha turadi? | 50 000 so'm | TEST-KT-003, 3-bo'lim |

## 📄 04_biznes_kredit.pdf bo'yicha savollar

| # | Savol | To'g'ri javob | Manba |
|---|-------|---------------|-------|
| 17 | Mikro biznes krediti foiz stavkasi qancha? | 22% (yillik) | TEST-KR-004, 2-bo'lim |
| 18 | Kichik biznes uchun maksimal kredit summasi? | 3 mlrd so'm | TEST-KR-004, 2-bo'lim |
| 19 | Biznes kredit uchun qanday hujjatlar kerak? | Ro'yxatdan o'tish guvohnomasi, soliq deklaratsiyasi, biznes-reja, moliyaviy hisobotlar, garov hujjatlari | TEST-KR-004, 3-bo'lim |
| 20 | Imtiyozli davr (grace period) qancha? | 6 oygacha | TEST-KR-004, 5-bo'lim |
| 21 | Qaysi kreditlar Kredit qo'mitasi tasdig'ini talab qiladi? | 1 mlrd so'mdan yuqori | TEST-KR-004, 4-bo'lim |

## 📄 05_valyuta_operatsiyalari.pdf bo'yicha savollar

| # | Savol | To'g'ri javob | Manba |
|---|-------|---------------|-------|
| 22 | USD sotish kursi qancha? | 12 700 so'm | TEST-VL-005, 1-bo'lim |
| 23 | Qaysi summadan valyuta operatsiyasida pasport kerak? | 3 000 AQSh dollari va undan yuqori | TEST-VL-005, 2-bo'lim |
| 24 | SWIFT o'tkazma komissiyasi qancha? | 0.3% (minimal 100 000 so'm) | TEST-VL-005, 3-bo'lim |
| 25 | Konvertatsiya komissiyasi qancha? | 0.2% | TEST-VL-005, 5-bo'lim |

---

## 🚫 Hallucination test savollari (javob hujjatda YO'Q)

Bu savollarga AI **"Javob mavjud emas"** deyishi kerak. Agar javob to'qib chiqarsa — bu xato (hallucination).

| # | Savol | Kutilgan javob |
|---|-------|----------------|
| H1 | Avtokredit foiz stavkasi qancha? | "Javob mavjud emas" (avtokredit hujjati yo'q) |
| H2 | Bankning prezidenti kim? | "Javob mavjud emas" |
| H3 | Depozit foiz stavkasi qancha? | "Javob mavjud emas" (depozit hujjati yo'q) |
| H4 | Filial necha soatda ochiladi? | "Javob mavjud emas" (ish vaqti hujjati yo'q) |
| H5 | 2027-yilda foiz stavka qanday bo'ladi? | "Javob mavjud emas" |

---

## 🌐 Aralash til testi (rus tilida savol, javob o'zbekcha hujjatdan)

| # | Savol (rus) | To'g'ri javob |
|---|-------------|---------------|
| R1 | Какая процентная ставка по ипотеке? | 18% (yillik) |
| R2 | Сколько хранятся документы идентификации? | 5 yil |

---

## ✅ Baholash usuli

Har bir javobni quyidagicha belgilang:
- **✓ To'g'ri** — javob aniq va manba to'g'ri
- **~ Qisman** — javob qisman to'g'ri yoki manba noaniq
- **✗ Noto'g'ri** — javob xato
- **⊘ Topa olmadi** — to'g'ri javob bor edi, lekin AI topolmadi
- **⚠ Hallucination** — AI to'qib chiqardi (eng xavfli!)

**Maqsad:** 25 ta asosiy savoldan 22+ to'g'ri (90%+), 5 ta hallucination testdan 5/5 "javob yo'q", hech qanday ⚠ bo'lmasligi kerak.
