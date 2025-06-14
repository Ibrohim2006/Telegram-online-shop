from modeltranslation.translator import register, TranslationOptions
from .models import Category, Product, ProductColor


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


@register(ProductColor)
class ProductColorTranslationOptions(TranslationOptions):
    fields = ('name',)
