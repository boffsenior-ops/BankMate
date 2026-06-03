"""
Synthetic demo seed script — creates users, branches, and 20 synthetic text
documents (stored in MinIO, metadata in PostgreSQL).

Run inside the Docker container:
    docker exec bankmate_backend python -m app.scripts.seed_demo
"""
import asyncio
import io
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.database import async_session_maker
from app.core.security import get_password_hash
from app.models.models import Branch, Document, RoleEnum, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Synthetic document content ────────────────────────────────────────────────
DOCUMENTS = [
    # --- Credit ---
    {
        "title": "Ipoteka kreditlash yo'riqnomasi",
        "category": "credit",
        "content": (
            "IPOTEKA KREDITLASH BO'YICHA ICHKI YO'RIQNOMA\n\n"
            "1. Kredit summasi: 50 000 000 so'mdan 5 000 000 000 so'mgacha.\n"
            "2. Foiz stavkasi: O'zbekiston Markaziy banki baza stavkasining 1.5 baravari.\n"
            "3. Muddat: 5 yildan 30 yilgacha.\n"
            "4. Boshlang'ich to'lov: kamida 20%.\n"
            "5. Talab qilinadigan hujjatlar: pasport, daromad ma'lumotnomai, garov mulki hujjatlari.\n"
            "6. Ko'rib chiqish muddati: 10 ish kuni.\n"
            "7. Imtiyozli dasturlar: yoshlar uchun 8% davlat subsidiyasi mavjud.\n"
        ),
    },
    {
        "title": "Kredit skoring modeli 2024",
        "category": "credit",
        "content": (
            "KREDIT SKORING MODELI — 2024 YANGILANGAN VERSIYA\n\n"
            "Baholash mezonlari:\n"
            "- Daromad barqarorligi: 30 ball\n"
            "- Kredit tarixi: 25 ball\n"
            "- Bandlik: 20 ball\n"
            "- Garov qiymati: 15 ball\n"
            "- Yosh va oilaviy ahvol: 10 ball\n\n"
            "Ball bo'yicha qaror:\n"
            "85-100: Avtomatik tasdiqlash\n"
            "70-84: Qo'shimcha tahlil\n"
            "55-69: Kollegial qaror\n"
            "55 dan past: Rad etish\n"
        ),
    },
    {
        "title": "Muddati o'tgan kreditlar bo'yicha tartib",
        "category": "credit",
        "content": (
            "MUDDATI O'TGAN KREDITLAR BILAN ISHLASH TARTIBI\n\n"
            "1-30 kun: SMS va qo'ng'iroq orqali eslatma.\n"
            "31-60 kun: Shaxsiy xabardorlik, qayta tuzish taklifi.\n"
            "61-90 kun: Kredit bo'limiga topshirish, garovni baholash.\n"
            "90+ kun: Yuridik bo'lim va NBKI'ga xabar berish, inkasso boshlash.\n"
            "Qayta tuzish shartlari: muddatni uzaytirish, foizni kamaytirish mumkin.\n"
        ),
    },
    {
        "title": "Kichik biznes kreditlash qo'llanmasi",
        "category": "credit",
        "content": (
            "KICHIK VA O'RTA BIZNES KREDITLASH\n\n"
            "Maqsadli auditoriya: Faoliyat muddati kamida 12 oy bo'lgan YaTT va MChJ.\n"
            "Kredit turlari: Aylanma mablag' uchun, asosiy vositalar uchun, eksport.\n"
            "Maksimal summa: 15 mlrd so'm.\n"
            "Foiz stavkasi: 19-24% yillik.\n"
            "Garov: ko'char va ko'chmas mulk, kafillik, bank kafolati.\n"
        ),
    },
    # --- AML / KYC ---
    {
        "title": "AML siyosati va protseduralar 2024",
        "category": "aml",
        "content": (
            "PULDAYDIRISH VA TERRORIZMNI MOLIYALASHTIRISHGA QARSHI KURASH SIYOSATI\n\n"
            "Qonuniy asos: O'zbekiston Respublikasining 2004-yil 26-avgustdagi 638-sonli Qonuni.\n\n"
            "CDD (Customer Due Diligence) talablari:\n"
            "- Barcha yangi mijozlar to'liq identifikatsiyadan o'tishi shart.\n"
            "- Yuridik shaxslar uchun benefitsar egasi aniqlanishi kerak.\n"
            "- Yuzaki tanishish (Simplified DD): kam xavfli mijozlar uchun.\n"
            "- Kuchaytirilgan tekshiruv (Enhanced DD): PEP, yuqori xavfli mamlakatlar.\n\n"
            "Shubhali operatsiyalarni aniqlash belgilari:\n"
            "1. Bir kunda 50 mln so'mdan ortiq naqd pul operatsiyalari.\n"
            "2. Biznes profiliga mos kelmaydigan operatsiyalar.\n"
            "3. Bir xil summalardagi takroriy o'tkazmalar.\n"
            "4. Taqiqlangan mamlakatlarga/dan o'tkazmalar.\n"
        ),
    },
    {
        "title": "KYC tekshiruv tartibi",
        "category": "aml",
        "content": (
            "MIJOZLARNI IDENTIFIKATSIYA QILISH TARTIBI (KYC)\n\n"
            "Jismoniy shaxslar uchun:\n"
            "- Pasport yoki ID karta (amal qilish muddati tekshiriladi)\n"
            "- PINFL va JShShIR\n"
            "- Yashash manzili tasdiqlovchi hujjat\n"
            "- Daromad manbai to'g'risidagi ma'lumot (10 mln so'mdan yuqori)\n\n"
            "Yuridik shaxslar uchun:\n"
            "- Davlat ro'yxatidan o'tish guvohnomasi\n"
            "- Ustav hujjatlari\n"
            "- Vakolatli shaxs hujjatlari\n"
            "- Benefitsar egasini tasdiqlash (25% ulushdan yuqori)\n\n"
            "Yangilash muddatlari: Yuqori xavf — har 6 oy, O'rta — har yil, Past — har 3 yil.\n"
        ),
    },
    {
        "title": "PEP (Siyosiy ta'sir o'tkazuvchi shaxslar) ro'yxati va tartib",
        "category": "aml",
        "content": (
            "SIYOSIY TA'SIR O'TKAZUVCHI SHAXSLAR (PEP) BILAN ISHLASH TARTIBI\n\n"
            "PEP toifalari:\n"
            "1. Davlat rahbarlari va hukumat a'zolari\n"
            "2. Parlamentariylar\n"
            "3. Oliy sud hakimlari\n"
            "4. Markaziy bank va davlat korxonalari rahbarlari\n"
            "5. Xalqaro tashkilotlar rahbarlari\n\n"
            "Majburiy talablar PEP uchun:\n"
            "- Yuqori rahbariyat tomonidan tasdiqlash\n"
            "- Kuchaytirilgan due diligence\n"
            "- Har 6 oyda monitoring\n"
            "- Barcha operatsiyalar uchun manbani tekshirish\n"
            "Oilaviy a'zolar ham PEP sifatida ko'rib chiqiladi.\n"
        ),
    },
    {
        "title": "Shubhali operatsiyalar haqida xabar berish tartibi",
        "category": "aml",
        "content": (
            "SHUBHALI OPERATSIYALAR TO'G'RISIDA XABAR BERISH (STR)\n\n"
            "Xabar berish muddati: Shubha paydo bo'lgandan keyin 3 ish kuni ichida.\n"
            "Xabar berilishi kerak bo'lgan organ: Moliyaviy Monitoring Qo'mitasi (MMQ).\n\n"
            "STR tuzilishi:\n"
            "1. Mijoz ma'lumotlari\n"
            "2. Operatsiya tavsifi\n"
            "3. Shubha sababi\n"
            "4. Xodimning xulosasi\n\n"
            "MUHIM: Mijozga STR yuborilganligi haqida xabar berish taqiqlanadi (tipping off).\n"
            "Xodimlar konfidensiallik to'g'risidagi majburiyatni imzolaydi.\n"
        ),
    },
    # --- Products ---
    {
        "title": "BankMate Omonat mahsulotlari katalogi",
        "category": "products",
        "content": (
            "OMONAT MAHSULOTLARI 2024\n\n"
            "1. 'Farovon' omonati\n"
            "   - Muddat: 3-36 oy\n"
            "   - Foiz: 20-24% yillik\n"
            "   - Minimal summa: 1 000 000 so'm\n"
            "   - Kapitallashtirish: Oylik\n\n"
            "2. 'Ishonch' dollar omonati\n"
            "   - Muddat: 6-24 oy\n"
            "   - Foiz: 5-7% yillik\n"
            "   - Minimal summa: 500 USD\n\n"
            "3. 'Oltin' bolalar omonati\n"
            "   - Muddat: 1-10 yil\n"
            "   - Foiz: 22% yillik\n"
            "   - Imtiyoz: Muddatga 1 yil qolsa 2% qo'shiladi\n"
        ),
    },
    {
        "title": "Plastik kartalar va xizmatlar",
        "category": "products",
        "content": (
            "BANK KARTALARI VA TO'LOV XIZMATLARI\n\n"
            "UZCARD kartasi:\n"
            "- Milliy to'lov tizimi\n"
            "- Yillik xizmat haqi: 30 000 so'm\n"
            "- ATM dan yechib olish: oyiga 3 martadan bepul\n\n"
            "HUMO kartasi:\n"
            "- Kengaytirilgan akseptans tarmog'i\n"
            "- Yillik: 50 000 so'm\n"
            "- Cashback: 1%\n\n"
            "VISA kartasi:\n"
            "- Xalqaro to'lovlar uchun\n"
            "- Yillik: 100 000 so'm\n"
            "- Xorijda yechib olish: 2% komissiya\n\n"
            "Raqamli bank: Mobil ilova orqali barcha operatsiyalar 24/7.\n"
        ),
    },
    {
        "title": "Pul o'tkazmalari va valyuta xizmatlari",
        "category": "products",
        "content": (
            "PUL O'TKAZMALARI VA VALYUTA XIZMATLARI\n\n"
            "Ichki o'tkazmalar: Bepul (bir kunlik limit: 100 mln so'm)\n\n"
            "Xalqaro o'tkazmalar:\n"
            "- SWIFT: 0.1% (min 25 USD, max 250 USD)\n"
            "- Western Union: 3.9%\n"
            "- MoneyGram: 3.5%\n\n"
            "Valyuta almashtirish:\n"
            "- Kurs: Markaziy bank kursi ± 5%\n"
            "- Limitlar: Jismoniy shaxslar uchun 5000 USD/kun\n"
            "- Hujjat: 1000 USD dan yuqori uchun pasport talab qilinadi\n\n"
            "Valyuta nazorati: Barcha $10 000 dan ortiq operatsiyalar qayd etiladi.\n"
        ),
    },
    # --- Cards ---
    {
        "title": "Kredit karta mahsulot tavsifi",
        "category": "cards",
        "content": (
            "KREDIT KARTASI MAHSULOT TAVSIFI\n\n"
            "BankMate Gold Kredit Karta:\n"
            "Kredit limiti: 5 mln — 50 mln so'm\n"
            "Grace davr: 55 kun (foizsiz)\n"
            "Foiz stavkasi: 28% yillik (grace o'tgandan keyin)\n"
            "Minimal to'lov: Qoldiqning 5% yoki 200 000 so'm\n"
            "Cashback: Supermarket — 2%, Kafе — 3%, Boshqalar — 1%\n\n"
            "Kredit karta olish talablari:\n"
            "- Yosh: 21-65\n"
            "- Rasmiy daromad: 3 mln so'mdan yuqori\n"
            "- Kredit tarixi: Salbiy emas\n"
            "- Hujjat: Pasport + daromad ma'lumotnomasi\n"
        ),
    },
    {
        "title": "Korporativ kartalar bo'yicha yo'riqnoma",
        "category": "cards",
        "content": (
            "KORPORATIV BANK KARTALARI\n\n"
            "Maqsad: Korporativ xarajatlarni boshqarish\n\n"
            "Turlari:\n"
            "1. Asosiy karta: Rahbariyat uchun, limit: 500 mln so'm\n"
            "2. Xodimlar kartasi: Individual limitlar, nazorat tizimi\n"
            "3. Virtual karta: Online xaridlar uchun\n\n"
            "Xususiyatlari:\n"
            "- Real-time xarajat monitoring\n"
            "- Kategoriyalar bo'yicha limit belgilash\n"
            "- Avtomatik hisobotlar\n"
            "- 1C va ERP tizimlariga integratsiya\n\n"
            "Xizmat haqi: Oyiga 150 000 so'm (10 tagacha karta)\n"
        ),
    },
    # --- Currency ---
    {
        "title": "Valyuta nazorati qoidalari",
        "category": "currency",
        "content": (
            "VALYUTA NAZORATI BO'YICHA ICHKI QOIDALAR\n\n"
            "Qonuniy asos: O'zbekiston Respublikasining 'Valyutani tartibga solish to'g'risida'gi qonuni.\n\n"
            "Rezidentlar uchun:\n"
            "- Xorijda hisob ochish: Markaziy bank ruxsati talab qilinadi\n"
            "- Valyuta kirimlarini 30 kun ichida so'mga konvertatsiya qilish majburiy\n"
            "- Eksport tushumi: 25% majburiy sotish (2024 yil)\n\n"
            "Norezidentlar uchun:\n"
            "- Kiritilgan kapitalning to'liq repatriatsiyasi mumkin\n"
            "- Dividendlar va foizlar: 10% soliq ushlab qolish\n\n"
            "Nazorat chegaralari:\n"
            "- Naqd valyuta import/eksporti: $10 000 (deklaratsiya)\n"
        ),
    },
    {
        "title": "Konvertatsiya xizmatlari tartib-qoidalari",
        "category": "currency",
        "content": (
            "VALYUTA KONVERTATSIYASI XIZMATI\n\n"
            "Ish vaqti: D-F 9:00-18:00, Sh 9:00-14:00\n\n"
            "Operatsiya chegaralari (jismoniy shaxslar):\n"
            "USD sotib olish: Kuniga 5 000 USD gacha\n"
            "USD sotish: Cheksiz (pasport talab qilinadi 1000 USD dan)\n\n"
            "Kurs belgilash:\n"
            "- Kurs har 30 daqiqada yangilanadi\n"
            "- Market making: bid-ask spread 0.5-1%\n"
            "- Katta summalarda muzokarali kurs\n\n"
            "Hujjatlar: 1000 USD dan yuqori uchun pasport + mablag' manbai.\n"
        ),
    },
    {
        "title": "Xalqaro hisob-kitob standartlari",
        "category": "currency",
        "content": (
            "XALQARO HISOB-KITOB STANDARTLARI\n\n"
            "SWIFT xizmatlari:\n"
            "- BIC kodi: BKUZUZ22\n"
            "- Correspondent banklar: Deutsche Bank, Citibank, Raiffeisen\n\n"
            "O'tkazma muddatlari:\n"
            "- SEPA (Yevropa): 1-2 ish kuni\n"
            "- SWIFT (dunyo): 2-5 ish kuni\n"
            "- Urgent (bir kun): +0.05% komissiya\n\n"
            "AML tekshiruvi: $1000 dan yuqori barcha xalqaro o'tkazmalar\n"
            "avtomatik skrinigdan o'tadi (OFAC, EU sanksion ro'yxatlari).\n"
        ),
    },
    # --- Regulations ---
    {
        "title": "Markaziy bank yo'riqnomasi: kapital yetarliligi",
        "category": "regulations",
        "content": (
            "MARKAZIY BANK YO'RIQNOMASI № 1-2024: KAPITAL YETARLILIGI\n\n"
            "Basel III talablari asosida:\n\n"
            "Koeffitsientlar:\n"
            "- CET1 (Asosiy kapital): Kamida 4.5%\n"
            "- Tier 1 kapital: Kamida 6%\n"
            "- Umumiy kapital: Kamida 8%\n"
            "- Bufer: +2.5% (kapital saqlov bufer)\n\n"
            "Likvidlik koeffitsientlari:\n"
            "- LCR (qisqa muddatli): Kamida 100%\n"
            "- NSFR (uzoq muddatli): Kamida 100%\n\n"
            "Hisobot: Har chorak oxirida Markaziy bankka topshiriladi.\n"
        ),
    },
    {
        "title": "Konsumer himoyasi qoidalari",
        "category": "regulations",
        "content": (
            "BANK XIZMATLARI ISTE'MOLCHILARINI HIMOYA QILISH\n\n"
            "Shikoyat ko'rib chiqish tartibi:\n"
            "1. Mijoz murojaat qiladi (telefon/email/shaxsan)\n"
            "2. Ro'yxatga olish: 1 ish kuni ichida\n"
            "3. Dastlabki javob: 3 ish kuni\n"
            "4. To'liq javob: 15 ish kuni\n"
            "5. Murakkab masalalar: 30 ish kuni\n\n"
            "Mijoz huquqlari:\n"
            "- To'liq ma'lumot olish huquqi\n"
            "- Shartnomadan 14 kun ichida voz kechish (muddatli mahsulotlar uchun)\n"
            "- Ombudsman orqali murojaat\n\n"
            "Shaffoflik: APR (yillik foiz stavkasi) barcha reklama materiallarida ko'rsatiladi.\n"
        ),
    },
    {
        "title": "FATCA va CRS talablari",
        "category": "regulations",
        "content": (
            "FATCA VA CRS TALABLARIGA MUVOFIQLIK\n\n"
            "FATCA (Amerika fuqarolari uchun):\n"
            "- AQSh fuqarolari va rezidentlari identifikatsiyasi majburiy\n"
            "- $10 000 dan ortiq hisoblar IRS'ga xabar qilinadi\n"
            "- W-9 va W-8BEN shakllarini to'ldirish\n\n"
            "CRS (Umumiy hisobot standarti):\n"
            "- 100+ mamlakatlar bilan avtomatik ma'lumot almashinuvi\n"
            "- Har yil 30 sentabrgacha hisobot topshiriladi\n"
            "- Barcha norezident hisoblar tekshiriladi\n\n"
            "Mas'ul bo'lim: Compliance va huquqiy bo'lim.\n"
        ),
    },
    {
        "title": "Kiberhavfsizlik talablari va hodisalarga javob berish",
        "category": "regulations",
        "content": (
            "KIBERHAVFSIZLIK SIYOSATI VA HODISALARGA JAVOB\n\n"
            "Xodimlar majburiyatlari:\n"
            "- Parolni 90 kunda o'zgartirish\n"
            "- 2FA barcha tizimlar uchun majburiy\n"
            "- Shubhali emaillarni IT xizmatiga xabar berish\n"
            "- USB qurilmalardan foydalanish taqiqlangan\n\n"
            "Hodisa toifalari:\n"
            "- P1 (Kritik): 15 daqiqa ichida javob\n"
            "- P2 (Yuqori): 1 soat\n"
            "- P3 (O'rta): 4 soat\n"
            "- P4 (Past): 24 soat\n\n"
            "Ma'lumotlar xavfsizligi: PCI DSS Level 1 va ISO 27001 sertifikati.\n"
        ),
    },
]


async def seed_demo():
    """Seed the database with branches, users, and synthetic documents."""
    async with async_session_maker() as db:
        # ── Branches ──────────────────────────────────────────────────────────
        from sqlalchemy import select as sa_select

        existing_branch = (await db.execute(sa_select(Branch).limit(1))).scalar_one_or_none()
        if not existing_branch:
            branches = [
                Branch(name="Bosh filial", code="B001", region="Toshkent"),
                Branch(name="Chilonzor filiali", code="B002", region="Toshkent"),
                Branch(name="Samarqand filiali", code="B003", region="Samarqand"),
                Branch(name="Namangan filiali", code="B004", region="Namangan"),
                Branch(name="Andijon filiali", code="B005", region="Andijon"),
            ]
            db.add_all(branches)
            await db.flush()
            for b in branches:
                await db.refresh(b)
            branch_id = branches[0].id
            logger.info("Created %d branches", len(branches))
        else:
            branch_id = existing_branch.id
            logger.info("Branches already exist")

        # ── Users ─────────────────────────────────────────────────────────────
        users_to_create = [
            ("admin_user", "admin@bankmate.local", "Admin1234!", "System Administrator", RoleEnum.ADMIN),
            ("content_user", "content@bankmate.local", "Content1234!", "Content Manager", RoleEnum.CONTENT_MANAGER),
            ("manager_user", "manager@bankmate.local", "Manager1234!", "Branch Manager", RoleEnum.BRANCH_MANAGER),
            ("auditor_user", "auditor@bankmate.local", "Auditor1234!", "System Auditor", RoleEnum.AUDITOR),
            ("staff_user", "staff@bankmate.local", "Staff1234!", "Bank Staff", RoleEnum.USER),
        ]
        created_users = 0
        for username, email, password, full_name, role in users_to_create:
            exists = (await db.execute(sa_select(User).where(User.username == username))).scalar_one_or_none()
            if not exists:
                db.add(User(
                    username=username, email=email,
                    password_hash=get_password_hash(password),
                    full_name=full_name, role=role,
                    branch_id=branch_id, is_active=True,
                ))
                created_users += 1
        await db.flush()
        logger.info("Created %d new users", created_users)

        # Find admin user id for uploaded_by
        admin = (await db.execute(sa_select(User).where(User.username == "admin_user"))).scalar_one_or_none()
        admin_id = admin.id if admin else None

        # ── Synthetic Documents ───────────────────────────────────────────────
        try:
            from app.services.documents.storage import upload_file_to_minio
            minio_available = True
        except Exception:
            minio_available = False
            logger.warning("MinIO not available, skipping file upload")

        created_docs = 0
        for doc_data in DOCUMENTS:
            existing = (
                await db.execute(sa_select(Document).where(Document.title == doc_data["title"]))
            ).scalar_one_or_none()
            if existing:
                continue

            file_path = f"synthetic/{doc_data['category']}/{doc_data['title'].replace(' ', '_')}.txt"

            if minio_available:
                try:
                    content_bytes = doc_data["content"].encode("utf-8")
                    file_path = upload_file_to_minio(
                        io.BytesIO(content_bytes),
                        f"{doc_data['title']}.txt",
                        "text/plain",
                    )
                except Exception as e:
                    logger.warning("MinIO upload failed for %s: %s", doc_data["title"], e)

            doc = Document(
                title=doc_data["title"],
                category=doc_data["category"],
                file_path=file_path,
                status="uploaded",
                version=1,
                uploaded_by=admin_id,
            )
            db.add(doc)
            created_docs += 1

        await db.commit()
        logger.info("Created %d synthetic documents", created_docs)
        print(
            f"\n✅ Demo seeding complete!\n"
            f"   Users created: {created_users}\n"
            f"   Documents created: {created_docs}\n\n"
            f"   Login credentials:\n"
            f"   - Admin:   admin_user / Admin1234!\n"
            f"   - Content: content_user / Content1234!\n"
            f"   - Staff:   staff_user / Staff1234!\n"
        )


if __name__ == "__main__":
    asyncio.run(seed_demo())
