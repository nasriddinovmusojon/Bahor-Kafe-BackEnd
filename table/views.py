from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from .models import Table, Product, Category, StockIn, StockOut
from .serializer import TableSerializer, ProductSerializer, CategorySerializer, CategoryMenuSerializer, \
    ProductFormSerializer, StockOutSerializer, StockInSerializer


class TableViewSet(viewsets.ModelViewSet):
    """
    Stol modeli uchun CRUD.

    Query params:
    - ?status=
    - ?is_active=
    """
    serializer_class = TableSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Table.objects.all().order_by("name")

        status_param = self.request.query_params.get("status")
        is_active_param = self.request.query_params.get("is_active")

        if status_param:
            queryset = queryset.filter(status=status_param)

        if is_active_param is not None:
            if is_active_param.lower() == "true":
                queryset = queryset.filter(is_active=True)
            elif is_active_param.lower() == "false":
                queryset = queryset.filter(is_active=False)

        return queryset


class CategoryViewSet(viewsets.ModelViewSet):
    """
    Kategoriya modeli uchun CRUD.

    Query params:
    - ?is_active=
    """
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Category.objects.all().order_by("name")

        is_active_param = self.request.query_params.get("is_active")

        if is_active_param is not None:
            if is_active_param.lower() == "true":
                queryset = queryset.filter(is_active=True)
            elif is_active_param.lower() == "false":
                queryset = queryset.filter(is_active=False)

        return queryset


class ProductViewSet(viewsets.ModelViewSet):
    """
    Mahsulot modeli uchun CRUD.

    Query params:
    - ?category=
    - ?is_active=
    - ?search=
    """
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Product.objects.select_related("category").all().order_by("name")

        category_param = self.request.query_params.get("category")
        is_active_param = self.request.query_params.get("is_active")
        search_param = self.request.query_params.get("search")

        if category_param:
            queryset = queryset.filter(category_id=category_param)

        if is_active_param is not None:
            if is_active_param.lower() == "true":
                queryset = queryset.filter(is_active=True)
            elif is_active_param.lower() == "false":
                queryset = queryset.filter(is_active=False)

        if search_param:
            queryset = queryset.filter(name__icontains=search_param.strip())

        return queryset



class MenuAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = Category.objects.filter(is_active=True)

        serializer = CategoryMenuSerializer(categories, many=True)

        return Response({
            "categories": serializer.data
        })



class ProductCreateUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # ➕ CREATE
    def post(self, request):
        serializer = ProductFormSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=400)

    # ✏️ UPDATE
    def put(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({"error": "Topilmadi"}, status=404)

        serializer = ProductFormSerializer(product, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=400)



class StockInViewSet(viewsets.ModelViewSet):
    queryset = StockIn.objects.all().order_by("-id")
    serializer_class = StockInSerializer


class StockOutViewSet(viewsets.ModelViewSet):
    queryset = StockOut.objects.all().order_by("-id")
    serializer_class = StockOutSerializer