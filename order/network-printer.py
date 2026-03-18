from escpos.printer import Network

def test_print():
    try:
        printer = Network(
            host="192.168.1.10",
            port=9100,
            timeout=10
        )

        printer.open()   # MUHIM!

        printer.text("TEST PRINT\n")
        printer.cut()

        printer.close()

        print("✅ Chop etildi")

    except Exception as e:
        print("❌ Xatolik:", e)