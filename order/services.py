from escpos.printer import Network
from escpos.exceptions import Error as EscposError
from django.conf import settings


class KitchenPrinterError(Exception):
    """
    Printer bilan bog'liq foydalanuvchiga tushunarli xatolar uchun umumiy exception.
    """
    pass


def print_kitchen_ticket(order):
    """
    Order ma'lumotlarini oshxona printeriga chiqaradi.
    Xatolar bo'lsa KitchenPrinterError qaytaradi.
    """
    printer_ip = getattr(settings, "PRINTER_IP", None)
    printer_port = int(getattr(settings, "PRINTER_PORT", 9100))
    printer_timeout = int(getattr(settings, "PRINTER_TIMEOUT", 10))

    if not printer_ip:
        raise KitchenPrinterError(
            "Printer IP manzili sozlanmagan. Administrator bilan bog'laning."
        )

    printer = None

    try:
        printer = Network(
            host=printer_ip,
            port=printer_port,
            timeout=printer_timeout,
        )

        # MUHIM: connectionni majburan ochamiz
        printer.open()

        # Header
        printer.set(align="center", bold=True, width=2, height=2)
        printer.text("YANGI BUYURTMA\n")

        printer.set(align="center", bold=False, width=1, height=1)
        printer.text("--------------------------------\n")

        # Order info
        printer.set(align="left", bold=True, width=1, height=1)
        printer.text(f"Buyurtma #: {order.id}\n")

        if getattr(order, "table", None):
            table_text = getattr(order.table, "number", None) or str(order.table)
            printer.text(f"Stol: {table_text}\n")

        waiter = getattr(order, "waiter", None)
        if waiter:
            waiter_name = (
                getattr(waiter, "full_name", None)
                or getattr(waiter, "name", None)
                or str(waiter)
            )
            printer.text(f"Ofitsiant: {waiter_name}\n")

        created_at = getattr(order, "created_at", None)
        if created_at:
            printer.text(f"Vaqt: {created_at.strftime('%d-%m-%Y %H:%M')}\n")

        printer.text("--------------------------------\n")

        # Items
        items = order.items.all()
        printed_any_item = False

        for index, item in enumerate(items, start=1):
            qty = getattr(item, "quantity", None) or getattr(item, "qty", 1)

            if hasattr(item, "product") and item.product:
                product_name = getattr(item.product, "name", None) or str(item.product)
            else:
                product_name = getattr(item, "name", None) or "NOMA'LUM MAHSULOT"

            note = getattr(item, "note", None) or getattr(item, "comment", None) or ""

            printer.set(align="left", bold=True, width=1, height=1)
            printer.text(f"{index}. {str(product_name).upper()} x{qty}\n")

            if note:
                printer.set(align="left", bold=False, width=1, height=1)
                printer.text(f"   Izoh: {note}\n")

            printer.text("\n")
            printed_any_item = True

        if not printed_any_item:
            raise KitchenPrinterError(
                "Buyurtmada chop etiladigan mahsulotlar topilmadi."
            )

        # Footer
        printer.text("--------------------------------\n")
        printer.set(align="center", bold=True, width=1, height=1)
        printer.text("OSHXONAGA YUBORILDI\n")

        printer.feed(3)
        printer.cut()

    except TimeoutError:
        raise KitchenPrinterError(
            "Printer javob bermayapti. Printer yoqilganini va tarmoqqa ulanganini tekshiring."
        )
    except ConnectionRefusedError:
        raise KitchenPrinterError(
            "Printer ulanishni rad etdi. Printer porti noto'g'ri yoki printer noto'g'ri sozlangan bo'lishi mumkin."
        )
    except EscposError as e:
        raise KitchenPrinterError(
            f"Printer bilan ishlashda xatolik yuz berdi: {e}"
        )
    except OSError as e:
        error_text = str(e).lower()

        if "network is unreachable" in error_text:
            raise KitchenPrinterError(
                "Printer tarmog'iga ulanib bo'lmadi. Qurilma boshqa Wi-Fi ga ulangan bo'lishi mumkin yoki printer tarmoqda emas."
            )
        elif "no route to host" in error_text:
            raise KitchenPrinterError(
                "Printer manziliga yetib bo'lmadi. Printer IP manzili noto'g'ri yoki printer tarmoqda ko'rinmayapti."
            )
        elif "timed out" in error_text:
            raise KitchenPrinterError(
                "Printer javob bermayapti. Printer yoqilganini va LAN kabel ulanganini tekshiring."
            )
        else:
            raise KitchenPrinterError(
                f"Printer bilan aloqa qilishda xatolik yuz berdi: {e}"
            )
    except Exception as e:
        raise KitchenPrinterError(
            f"Chek chiqarishda kutilmagan xatolik yuz berdi: {e}"
        )
    finally:
        if printer:
            try:
                printer.close()
            except Exception:
                pass