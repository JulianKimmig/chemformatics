import os

from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.views import View
from djangobase.jsonconfig import JsonConfig

from scratchtester.models import Measurement, CsvStructure
from scratch_reader import ScratchReader
from settings import MEDIA_ROOT


class MainPage(View):
    def get(self, request):
        data = {"measurements": Measurement.objects.all()}
        return render(request, "main.html", data)


class MeasurementTabbed(View):
    def get(self, request, id):
        measurement = Measurement.objects.get(id=id)
        measurement.options = JsonConfig(data=measurement.options)
        data = {"measurement": measurement, "csv_strucs": CsvStructure.objects.all()}
        return render(request, "measurment_tabbed.html", data)


class MeasurementView(View):
    siteorder = [
        "start",
        "structure",
        "interpolation",
        "correction",
        "correction",
        "3d",
    ]

    def get(self, request, id, option):
        if id == 0:
            measurement = Measurement.objects.create()
            return self.get(request, measurement.id, "start")

        measurement = Measurement.objects.get(id=id)
        measurement.options = JsonConfig(data=measurement.options)
        data = {"measurement": measurement, "csv_strucs": CsvStructure.objects.all()}
        return render(request, "measurment_" + option + ".html", data)

    def post(self, request, id, option):
        measurement = Measurement.objects.get(id=id)
        measurement.options = JsonConfig(data=measurement.options)

        recalc = False
        if "name" in request.POST:
            measurement.name = request.POST.get("name", measurement.name)
        if "raw_data" in request.FILES:
            myfile = request.FILES["raw_data"]
            fs = FileSystemStorage(os.path.join(MEDIA_ROOT, "raw"))
            filename = fs.save(myfile.name, myfile)
            print(filename)
            measurement.raw_data = filename
            recalc = True

        if "raw_structure" in request.POST:
            if measurement.raw_structure.id != int(request.POST["raw_structure"]):
                print(
                    "B",
                    measurement.raw_structure.id,
                    request.POST["raw_structure"],
                    measurement.raw_structure.id != request.POST["raw_structure"],
                )
                recalc = True
                measurement.raw_structure = CsvStructure.objects.get(
                    id=request.POST["raw_structure"]
                )

        if not os.path.exists(
            os.path.join(MEDIA_ROOT, "interpolated", measurement.raw_data)
        ):
            recalc = True

        sr = ScratchReader(options=measurement.options)
        for k, v in request.POST.items():
            if k.startswith("opt_"):
                l = k[4:].split(",")
                if l[0] == "interpolation":
                    v, n = measurement.options.put(*l, value=v, testtype=True)
                    recalc = recalc or n
        if recalc:
            sr.read_raw(
                os.path.join(MEDIA_ROOT, "raw", measurement.raw_data),
                structure=measurement.raw_structure.name,
            )
            sr.interpolate()
            sr.save_interpolated(
                os.path.join(MEDIA_ROOT, "interpolated", measurement.raw_data)
            )

        measurement.options = measurement.options.to_json()
        measurement.save()

        return redirect(
            "scratchtester:measurment",
            id=measurement.id,
            option=self.siteorder[self.siteorder.index(option) + 1],
        )


class MeasurementData(View):
    def post(self, request, id, data):
        measurement = Measurement.objects.get(id=id)
        measurement.options = JsonConfig(data=measurement.options)
        if data == "raw":
            myfile = request.FILES["raw_data"]
            fs = FileSystemStorage(os.path.join(MEDIA_ROOT, "raw"))
            fs.delete(measurement.raw_data)
            measurement.raw_data = fs.save(myfile.name, myfile)

        measurement.options = measurement.options.to_json()
        measurement.save()
        return JsonResponse({"success": True})
