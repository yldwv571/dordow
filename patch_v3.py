# -*- coding: utf-8 -*-
"""
NIGHT MAFIA — ADDON v3 avtomatik o'rnatuvchi.

ISHLATISH (mafbot.py shu fayl bilan bir papkada bo'lsin):
    python patch_v3.py
yoki boshqa nomli fayl uchun:
    python patch_v3.py bot.py

Nima qiladi:
  1) mafbot.py dan zaxira nusxa oladi (mafbot.py.bak)
  2) ADDON v3 ni to'g'ri joyga (ensure_https dan oldin) qo'yadi
  3) Sintaksisni tekshiradi; xato bo'lsa fayl o'zgarmaydi
Ikki marta ishlatsangiz ham xavfsiz (qayta qo'shmaydi).
"""
import os, shutil, sys

TARGET = sys.argv[1] if len(sys.argv) > 1 else "mafbot.py"
MARK = "async def ensure_https():"

BLOCK = r'''
# ═══════════════════════════════════════════════════════════════════════════
#  NIGHT MAFIA — ADDON v3
#  NightCoin 100/100 · dollar xaridi (olmos/Stars) · /boylar faqat adminlar ·
#  tugma ranglari · premium emoji paketlari · operator javobi tuzatilgan
# ═══════════════════════════════════════════════════════════════════════════
r3 = Router()                                   # r2 dan ham oldin ishlaydi
dp.include_router(r3)
try:
    dp.sub_routers.remove(r3)
    dp.sub_routers.insert(0, r3)
except Exception:
    logging.warning("r3 router ustuvorligini o'rnatib bo'lmadi")

# ───────── 1) NightCoin: sotib olish 100 💎, sotish 100 💎 ─────────
NC_BUY, NC_SELL = 100, 100

# ───────── 2) Premium emoji paketlari (ID lar avtomatik olinadi) ─────────
EMOJI_PACKS = ["FinanceEmoji", "chatmaf_by_TgEmojiBot", "pk_6172168_by_Ctikerubot",
               "AR_PREMIUM", "gifts_emoji_by_gifts_changes_bot", "HalloweenTeamEmoji"]
_TGE = re.compile(r"(<tg-emoji\b.*?</tg-emoji>)", re.S)


def prem(text):
    """Oddiy emoji -> premium emoji (tg-emoji ichidagilarga tegmaydi; 1 xabarda max 90 ta)."""
    if not PE_RE or not isinstance(text, str): return text
    cnt = [0]

    def rep(m_):
        if cnt[0] >= 90: return m_.group(0)
        cnt[0] += 1
        return f'<tg-emoji emoji-id="{PE[m_.group(0)]}">{m_.group(0)}</tg-emoji>'
    parts = _TGE.split(text)
    for i in range(0, len(parts), 2): parts[i] = PE_RE.sub(rep, parts[i])
    return "".join(parts)


def _emoji_variants(ch):
    base = ch.replace("\ufe0f", "")
    out = {ch}
    if base and not all(ord(x) < 128 for x in base):     # "#", "1" kabi oddiy belgilarni almashtirmaymiz
        out |= {base, base + "\ufe0f"}
    return out


async def load_emoji_packs():
    found = {}
    for nm in EMOJI_PACKS:
        try: ss = await bot.get_sticker_set(nm)
        except Exception as e:
            logging.warning("Emoji paketi o'qilmadi %s: %s", nm, e); continue
        for st in ss.stickers:
            if getattr(st, "custom_emoji_id", None) and st.emoji:
                for v in _emoji_variants(st.emoji): found.setdefault(v, st.custom_emoji_id)
    manual = {}
    try:
        if os.path.exists("premium_emoji.json"): manual = json.load(open("premium_emoji.json", encoding="utf-8"))
    except Exception: manual = {}
    if found:
        d = dict(found); d.update(manual); set_pe(d)      # qo'lda saqlanganlar ustun turadi
        logging.info("Premium emoji yuklandi: %d ta", len(PE))
    return len(found)


@r3.message(Command("emojipack"))
async def cmd_emojipack(m: Message):
    if not (m.from_user and is_admin(m.from_user.id)): return
    n = await load_emoji_packs()
    await m.reply(f"✅ Paketlardan {n} ta emoji topildi. Jami faol: {len(PE)} ta." if n
                  else "⚠️ Paketlar o'qilmadi. Paket nomlarini tekshiring.")


# ───────── 3) Tugmalarga rang (ko'k / yashil / qizil) ─────────
_NEG = ("❌", "⬅️", "orqaga", "назад", "back", "rad ", "rad etish", "yo'q", "нет", "o'chir", "to'xtat", "🔴", "💔", "🚫", "qaytish", "chetlat")
_POS = ("✅", "sotib ol", "qabul", "qo'shil", "🎁", "🟢", "💕", "купить", "buy", "yes", "да")


def _pick_style(b):
    t_ = (b.text or "").lower()
    if any(x in t_ for x in _NEG): return "danger"
    if any(x in t_ for x in _POS): return "success"
    return "primary"


def color_markup(mk):
    changed = False; rows = []
    for row in mk.inline_keyboard:
        nr = []
        for b in row:
            if getattr(b, "style", None): nr.append(b)
            else: nr.append(b.model_copy(update={"style": _pick_style(b)})); changed = True
        rows.append(nr)
    return mk.model_copy(update={"inline_keyboard": rows}) if changed else mk


class StyleMW(BaseRequestMiddleware):
    async def __call__(self, make_request, bot_, method):
        mk = getattr(method, "reply_markup", None)
        if _HAS_STYLE and isinstance(mk, InlineKeyboardMarkup):
            try: return await make_request(bot_, method.model_copy(update={"reply_markup": color_markup(mk)}))
            except TelegramBadRequest: pass
        return await make_request(bot_, method)


bot.session.middleware(StyleMW())

# ───────── 4) /boylar — faqat bot adminlari va egasi, ismlar bosiladigan ─────────
@r3.message(C("boylar"))
async def boylar3(m: Message):
    if not (m.from_user and is_admin(m.from_user.id)): return
    ids = ",".join(str(int(i)) for i in ADMIN_IDS) or "0"
    mon = db.execute(f"SELECT id,name,money FROM users WHERE blocked=0 AND id NOT IN ({ids}) AND money>0 ORDER BY money DESC LIMIT 15").fetchall()
    dia = db.execute(f"SELECT id,name,diamonds FROM users WHERE blocked=0 AND id NOT IN ({ids}) AND diamonds>0 ORDER BY diamonds DESC LIMIT 15").fetchall()
    t1 = "\n".join(f"{i}. {lk(x['id'], x['name'])} — {n_(x['money'])} 💶" for i, x in enumerate(mon, 1)) or "—"
    t2 = "\n".join(f"{i}. {lk(x['id'], x['name'])} — {n_(x['diamonds'])} 💎" for i, x in enumerate(dia, 1)) or "—"
    await m.answer(f"💰 <b>Eng boy o'yinchilar (pul)</b>\n\n{t1}\n\n💎 <b>Eng boy o'yinchilar (olmos)</b>\n\n{t2}")


# ───────── 5) Xarid qilish 💵: Olmos orqali / Stars orqali ─────────
DOLLAR_D = {200: 1, 800: 4, 1600: 8, 2000: 10, 5000: 25, 10000: 40}        # pul: olmos
DOLLAR_S = {200: 3, 1000: 15, 2000: 30, 5000: 60, 7000: 100, 100000: 150}   # pul: stars


@r3.callback_query(F.data == "m:buym")
async def m_buym3(c: CallbackQuery):
    uid = c.from_user.id; b = InlineKeyboardBuilder()
    b.button(text="💎 Olmos orqali dollar", callback_data="bd:d")
    b.button(text="⭐ Stars orqali dollar", callback_data="bd:s")
    b.button(text=tt(uid, "back"), callback_data="m:profile"); b.adjust(1)
    await sedit(c, "💵 <b>Xarid qilish</b>\n\nDollarni qaysi usulda olmoqchisiz?", b.as_markup()); await c.answer()


def _bd_view(uid, a):
    b = InlineKeyboardBuilder()
    if a == "d":
        for money, d in DOLLAR_D.items(): b.button(text=f"💵 {money} - 💎 {d}", callback_data=f"dd:{money}")
        txt = f"Xarid qilish 💵\n\n💎 Olmos evaziga dollar xarid qilishingiz mumkin!\n\n💎 Olmosingiz: {n_(U(uid)['diamonds'])}"
    else:
        for money, s in DOLLAR_S.items(): b.button(text=f"💵 {money} $ - ⭐ {s}", callback_data=f"ds:{money}")
        txt = "💵 Qancha dollar olmoqchisiz?\n\n⭐ Stars orqali to'g'ridan-to'g'ri dollar xarid qiling!"
    b.adjust(2); b.row(InlineKeyboardButton(text=tt(uid, "back"), callback_data="m:buym"))
    return txt, b.as_markup()


@r3.callback_query(F.data.startswith("bd:"))
async def cb_bd(c: CallbackQuery):
    a = c.data[3:]
    if a not in ("d", "s"): return await c.answer()
    t_, k = _bd_view(c.from_user.id, a); await sedit(c, t_, k); await c.answer()


@r3.callback_query(F.data.startswith("dd:"))
async def cb_dd(c: CallbackQuery):
    uid = c.from_user.id
    try: money = int(c.data[3:])
    except ValueError: return await c.answer()
    if money not in DOLLAR_D: return await c.answer()
    price = DOLLAR_D[money]
    if U(uid)["diamonds"] < price: return await c.answer(tt(uid, "no_dia"), show_alert=True)
    A(uid, "diamonds", -price); A(uid, "money", money)
    await c.answer(f"✅ +{n_(money)} 💶 hisobingizga qo'shildi!", show_alert=True)
    t_, k = _bd_view(uid, "d"); await sedit(c, t_, k)


@r3.callback_query(F.data.startswith("ds:"))
async def cb_ds(c: CallbackQuery):
    try: money = int(c.data[3:])
    except ValueError: return await c.answer()
    if money not in DOLLAR_S: return await c.answer()
    await bot.send_invoice(c.from_user.id, title=f"{n_(money)} 💶 dollar", description="Stars orqali dollar xaridi",
                           payload=f"usd:{money}", currency="XTR", prices=[LabeledPrice(label=f"{money} dollar", amount=DOLLAR_S[money])])
    await c.answer()


@r3.message(F.successful_payment.invoice_payload.startswith("usd:"))
async def paid_usd(m: Message):
    try: money = int(m.successful_payment.invoice_payload.split(":")[1])
    except Exception: return
    if money not in DOLLAR_S: return
    A(m.from_user.id, "money", money)
    await m.answer(f"✅ To'lov qabul qilindi! +{n_(money)} 💶")


# ───────── 6) Buyruqlar menyusi + emoji paketlarini yuklash (bot ishga tushganda) ─────────
@dp.startup()
async def _v3_startup():
    await load_emoji_packs()
    gap = [("start", "O'yinni boshlash"), ("game", "O'yin yaratish"), ("vsgame", "Jamoaviy o'yin (VS)"), ("roles", "O'yin rollarini ko'rish"),
           ("leave", "O'yindan chiqish"), ("sozlamalar", "Sozlamalarni ochish"), ("stop", "O'yinni to'xtatish"), ("gtop", "Geroylar reytingi"),
           ("send", "Olmos tarqatish"), ("money", "Pul tarqatish / o'tkazish"), ("give", "Olmos o'tkazish"), ("change", "Olmos sovg'a o'yini"),
           ("tgeroy", "Geroyni sotish"), ("mypara", "Paralarim"), ("para", "Para qo'shish"),
           ("top", "Umrlik reyting"), ("top7", "Haftalik reyting"), ("top30", "Oylik reyting"), ("top1", "Kunlik reyting"), ("boylar", "Eng boylar")]
    try: await bot.set_my_commands([BotCommand(command=c_, description=d_) for c_, d_ in gap], scope=BotCommandScopeAllGroupChats())
    except Exception: logging.exception("v3 buyruqlar o'rnatilmadi")


# ───────── 7) Operator javobi (reply) — status kutishdan ustun turadi ─────────
@r3.message(is_sup_reply, F.text | F.photo)
async def sup_reply3(m: Message):
    WAIT.pop(m.from_user.id, None)        # qotib qolgan "status" kutishini tozalaydi
    await admin_support_reply(m)          # foydalanuvchiga botda + web chatda yuboradi
'''


def main():
    if not os.path.exists(TARGET):
        print(f"❌ {TARGET} topilmadi. Bu faylni mafbot.py bilan bir papkaga qo'ying.")
        return
    src = open(TARGET, encoding="utf-8").read()
    if "ADDON v3" in src:
        print("ℹ️ ADDON v3 allaqachon o'rnatilgan. Hech narsa o'zgarmadi.")
        return
    if "ADDON v2" not in src:
        print("❌ Faylda ADDON v2 topilmadi. Avval ADDON v2 qo'yilgan bo'lishi kerak.")
        return
    if MARK not in src:
        print(f"❌ '{MARK}' qatori topilmadi.")
        return
    i = src.index(MARK)
    new = src[:i].rstrip() + "\n\n\n" + BLOCK.strip("\n") + "\n\n\n" + src[i:]
    try:
        compile(new, TARGET, "exec")
    except SyntaxError as e:
        print(f"❌ Sintaksis xatosi (fayl o'zgarmadi): qator {e.lineno}: {e.msg}")
        return
    shutil.copy(TARGET, TARGET + ".bak")
    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(new)
    print(f"✅ Tayyor! ADDON v3 {TARGET} ichiga qo'shildi. Zaxira: {TARGET}.bak")
    print("Endi botni qayta ishga tushiring:  python mafbot.py")


if __name__ == "__main__":
    main()
