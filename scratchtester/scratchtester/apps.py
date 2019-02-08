from django.apps import AppConfig


class ScratchtesterConfig(AppConfig):
    name = "scratchtester"

    def ready(self):

        from djangobase.settings import CONFIG

        if CONFIG.get("Apps", self.name, "ws", default=False):
            from djangobase import routing
            from scratchtester import urls

            routing.append_routing(urls.websockets)

        from scratchtester.models import CsvStructure

        csvstruc, new = CsvStructure.objects.get_or_create(name="XYZ matrix")
        if new:
            csvstruc.html = (
                "<tr><th></th><th>X1</th><th>X2</th></tr>"
                "<tr><th>Y1</th><td>Z11</td><td>Z21</td></tr>"
                "<tr><th>Y2</th><td>Z12</td><td>Z22</td></tr>"
            )
            csvstruc.save()

        csvstruc, new = CsvStructure.objects.get_or_create(name="YZYZ")
        if new:
            csvstruc.html = (
                "<tr><th colspan='2'>X1</th><th colspan='2'>X2</th></tr>"
                "<tr><td>Y11</td><td>Z11</td><td>Y21</td><td>Z21</td></tr>"
                "<tr><td>Y12</td><td>Z12</td><td>Y22</td><td>Z22</td></tr>"
            )
            csvstruc.save()
