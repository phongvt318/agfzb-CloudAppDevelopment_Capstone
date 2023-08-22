from django.contrib import admin
# import new models 
from .models import CarMake, CarModel

# create CarModelInline class
class CarModelInline(admin.StackedInline):
    model = CarModel
    extra = 5

# create CarModelAdmin class
class CarMakeAdmin(admin.ModelAdmin):
    inlines = [CarModelInline]

# register CarMakeAdmin class with CarModelInline
admin.site.register(CarMake, CarMakeAdmin)

# register CarModel class
admin.site.register(CarModel)