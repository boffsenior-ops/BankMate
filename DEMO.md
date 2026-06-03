# BankMate — 5-daqiqalik Demo Stsenariyi

> **Maqsad:** Mahalliy serverlarda ishlaydigan RAG (Retrieval-Augmented Generation) tizimini namoyish etish.  
> **Auditoriya:** Bank rahbariyati, IT direktori, sarmoyadorlar.  
> **Muhit:** `http://localhost:3000`

---

## ⏱️ Demo grafigi (5 daqiqa)

### Daqiqa 1 — Tizimga kirish va interfeys

1. Brauzerda `http://localhost:3000` ni oching.
2. Login sahifasi ko'rinadi — tilni **O'zbekcha** / **Русский** ga o'zgartiring.
3. Admin sifatida kiring:
   - Username: `admin_user`
   - Password: `Admin1234!`
4. **`/chat`** sahifasiga yo'naltiriladi.

> 💬 *"Tizim to'liq mahalliy — cloud yoki internet kerak emas. Bank xodimi o'z kompyuterida ishlaydi."*

---

### Daqiqa 2 — RAG javoblari (Chatbot)

Chat sahifasida quyidagi savollarni birin-ketin bering:

**Savol 1 — Kredit:**
```
Ipoteka kreditining minimal boshlang'ich to'lovi qancha?
```
> Kutilgan: 20% deb javob beradi, hujjat sahifasi ko'rsatiladi.

**Savol 2 — AML/KYC:**
```
PEP mijoz bilan ishlashda qanday talablar mavjud?
```
> Kutilgan: Kuchaytirilgan due diligence, 6 oylik monitoring talablarini sanab beradi.

**Savol 3 — Bazada yo'q ma'lumot:**
```
BankMate nechchi yilda tashkil topgan?
```
> Kutilgan: *"Ushbu ma'lumot bazadagi hujjatlarda mavjud emas."* — AI o'ylab topib javob bermaydi.

> 💬 *"AI faqat tasdiqlanган bank hujjatlari asosida javob beradi. Manba va sahifa raqami doim ko'rsatiladi."*

---

### Daqiqa 3 — Manbalar (Citations)

1. Javob ostidagi **ko'k badge**larni ko'rsating.
2. Biror badge'ni bosing — modal ochiladi, qaysi hujjat, qaysi sahifadan ekanini ko'rsating.
3. Feedback tugmalarini (👍 / 👎) bosing.

> 💬 *"Har bir javobni xodim tekshira oladi — bu aniq va auditlanadigan tizim."*

---

### Daqiqa 4 — Admin panel

`http://localhost:3000/admin` ni oching (yoki navigatsiya panelidan).

**Dashboard:**
- Foydalanuvchilar, hujjatlar, indekslangan hujjatlar sonini ko'rsating.

**Hujjatlar sahifasi (`/admin/documents`):**
- Statuslar: indexed / uploaded / processing.
- Yangi hujjat yuklash formasi + drag-and-drop demo.

**Foydalanuvchilar sahifasi (`/admin/users`):**
- Turli rollar: ADMIN, CONTENT_MANAGER, USER.
- "Yangi foydalanuvchi" dialogini oching, to'ldiring (submit qilmasa ham bo'ladi).

**Audit log sahifasi (`/admin/audit`):**
- LOGIN_SUCCESS, DOCUMENT_UPLOADED, USER_CREATED yozuvlarini ko'rsating.
- CSV export tugmasini bosing — fayl yuklab olinadi.

> 💬 *"Har bir harakat qayd etiladi — kim, qachon, nima qildi. Compliance va monitoring uchun tayyor."*

---

### Daqiqa 5 — Arxitektura va xulosa

**Qisqa arxitektura sharhi:**

```
Browser → Next.js (port 3000)
             ↓ httpOnly cookie auth
       FastAPI Backend (port 8000)
             ↓ RAG pipeline
       OpenAI Embeddings → Qdrant Vector DB
       Anthropic Claude → Streaming javob
             ↓ metadata
       PostgreSQL + Redis + MinIO
```

**Asosiy afzalliklar:**
| Xususiyat | BankMate |
|-----------|----------|
| Ma'lumotlar joylashuvi | 100% mahalliy |
| AI modeli | Claude 3.5 Sonnet |
| Javob manbalari | Doim ko'rsatiladi |
| Til | O'zbek + Rus |
| Audit | Har bir harakat |
| RBAC | 5 ta rol |

---

## 🔐 Test foydalanuvchilari

| Username | Password | Rol |
|----------|----------|-----|
| `admin_user` | `Admin1234!` | ADMIN |
| `content_user` | `Content1234!` | CONTENT_MANAGER |
| `manager_user` | `Manager1234!` | BRANCH_MANAGER |
| `auditor_user` | `Auditor1234!` | AUDITOR |
| `staff_user` | `Staff1234!` | USER |

---

## 📂 Test hujjatlar (20 ta)

| Kategoriya | Soni | Misollar |
|------------|------|---------|
| `credit` | 4 | Ipoteka, skoring, muddati o'tgan, SMB |
| `aml` | 4 | AML siyosat, KYC, PEP, STR |
| `products` | 3 | Omonatlar, kartalar, o'tkazmalar |
| `cards` | 2 | Kredit karta, korporativ |
| `currency` | 3 | Nazorat, konvertatsiya, xalqaro |
| `regulations` | 4 | Kapital, konsumer, FATCA, kiberhavfsizlik |

---

## 🧪 Tizimni tekshirish buyruqlari

```bash
# Barcha konteynerlar holati
docker ps

# Backend salomatligi
curl http://localhost:8000/health

# Prometheus metrikalari
curl http://localhost:8000/metrics

# Seed script qayta ishlatish (agar kerak)
docker exec bankmate_backend python -m app.scripts.seed_demo
```

---

## 🗺️ Keyingi bosqich (Pilot)

- [ ] Real bank hujjatlarini yuklash (ishonch shartnomasi bilan)
- [ ] Active Directory / SSO integratsiya
- [ ] Kubernetes deployment (52 filial uchun)
- [ ] Monitoring dashboard (Grafana + Prometheus)
- [ ] Mobile app (React Native)
- [ ] Uzbek LLM fine-tuning
