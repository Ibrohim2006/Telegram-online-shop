from modeltranslation.translator import translator, TranslationOptions
from .models import Category, Product, ProductColor

class CategoryTranslationOptions(TranslationOptions):
    fields = ('name',)

class ProductTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

class ProductColorTranslationOptions(TranslationOptions):
    fields = ('name',)

translator.register(Category, CategoryTranslationOptions)
translator.register(Product, ProductTranslationOptions)
translator.register(ProductColor, ProductColorTranslationOptions)
