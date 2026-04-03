from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TableViewSet, ProductViewSet, CategoryViewSet, MenuAPIView, ProductCreateUpdateAPIView, \
    StockInViewSet, StockOutViewSet
from rest_framework.authtoken.views import obtain_auth_token

router = DefaultRouter()
router.register(r'table', TableViewSet, basename='table')
router.register(r'category', CategoryViewSet, basename='category')
router.register(r'product', ProductViewSet, basename='product')
router.register("kirim", StockInViewSet)
router.register("chiqim", StockOutViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('token/', obtain_auth_token, name='api_token_auth'),
    path("menu/", MenuAPIView.as_view(), name="menu"),# faqat 'token/' yoziladi
    path("product/create/", ProductCreateUpdateAPIView.as_view()),
    path("product/<int:pk>/update/", ProductCreateUpdateAPIView.as_view())
]

# bitta APi, 1-category uchun crud metodlari bo'lishi kerak,✅
# menu ovqatlarni kiritadigan joy bo'lishi kerak, faqat narxi bo'ladi , nomi bo'ladi, categoriyasi bo'ladi✅
# ovqatni category, narxi, nomi bo'ladi✅
#menu uchun  crud metodi yozib qo'yaveraman✅
# Xodmlar- crud api login parol bo'lishi kerak, lavozimi bo'ladi, offitsiant, oshpaz, kassir, boshliq✅
# bitta API kerak ovqatlarni catecgryni chiqarib beradigan, ovqatlarni category bo'yicha filtrleydigan API✅

# buyurtma qabul qiladigan API bo'lishi kerak,ovqat id, ovqat nomi, soni, mehmon soni, category id, category name, keyin status default, yoki vaqtincha saqlash, buyurtma turi, olib ketish, agar u tugmani bossa sent  to kitchen oshxonaga yuborish qilib qo'yish kerak

#Bitta API buyurtmani qabul qiladi

# Oshxona uchun bitta API bunda barcha orderlarni ko'rsatish kerak statusi sent to kitchen bo'lishi kerak STATUS_SENT_TO_KITCHEN;

# (STATUS_COOKING, 'Tayyorlanmoqda'),

# Yana bitta API put API orderni statusini o'zgartirib turadi NEW = "NEW", "Yangi",
#         COOKING = "COOKING", "Tayyorlanmoqda",
#         READY = "READY", "Tayyor".

#Stol ham yaratish kerak, Stollarni ko'radigan GET API kerak
 # to'lov qilish uchun chek chiqarish tugmadsini bosish kerak, to'lov turini tanlaydi, statusini paytga o'zgartirib qo'yadi