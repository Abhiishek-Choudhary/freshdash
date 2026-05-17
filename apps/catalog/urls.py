from django.urls import path

from apps.catalog import views

urlpatterns = [
    path("stores/<uuid:store_id>/products", views.StoreProductsView.as_view()),
    path("products/<uuid:product_id>", views.ProductDetailView.as_view()),
    path("products/search", views.ProductSearchView.as_view()),
    path("products/scan", views.ProductScanView.as_view()),
    path("products/<uuid:product_id>/related", views.RelatedProductsView.as_view()),
    path("vendor/products", views.VendorProductListCreateView.as_view()),
    path("vendor/products/<uuid:product_id>", views.VendorProductDetailView.as_view()),
]
