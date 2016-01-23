from django.contrib import admin
from books.models import BookType, Author, Book


class BookTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "creation_date")
    list_filter = ("creation_date", )
    search_fields = ("name", )
    list_per_page = 5


class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name", "image", "creation_date")


class BookAdmin(admin.ModelAdmin):
    list_display = ("name", "author")
    list_filter = ("author",)
    search_fields = ("name", "author__name")



admin.site.register(BookType, BookTypeAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Book, BookAdmin)