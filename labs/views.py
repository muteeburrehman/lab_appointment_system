from rest_framework import viewsets
from .models import Laboratory, LabTest
from .serializers import LaboratorySerializer, LabTestSerializer

class LaboratoryViewSet(viewsets.ModelViewSet):
    queryset = Laboratory.objects.all()
    serializer_class = LaboratorySerializer

class LabTestViewSet(viewsets.ModelViewSet):
    queryset = LabTest.objects.all()
    serializer_class = LabTestSerializer