from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LaboratoryViewSet, LabTestViewSet

router = DefaultRouter()
router.register(r'laboratories', LaboratoryViewSet)
router.register(r'lab-tests', LabTestViewSet)

urlpatterns = [
    path('', include(router.urls)),
]