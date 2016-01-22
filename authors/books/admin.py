from django.contrib import admin

from books.models import BookType, Author, Book


class BookTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "creation_date")
    list_filter = ("creation_date", )


class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name", "image", "creation_date")


class BookAdmin(admin.ModelAdmin):
    list_display = ("name", "author")
    list_filter = ("author",)


admin.site.register(BookType, BookTypeAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Book, BookAdmin)