from allauth.headless.spec.views import OpenAPIHTMLView


class AllauthSwaggerView(OpenAPIHTMLView):
    def get_template_names(self):
        return ["headless/spec/swagger_cdn.html"]


class AllauthRedocView(OpenAPIHTMLView):
    def get_template_names(self):
        return ["headless/spec/redoc_cdn.html"]
