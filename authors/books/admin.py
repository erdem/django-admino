from django.contrib import admin
from books.models import BookType, Author, Book


class BookTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "new_col", "creation_date")
    list_filter = ("creation_date", )

    def new_col(self, obj):
        return "145"

class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name", "image", "creation_date")


class BookAdmin(admin.ModelAdmin):
    list_display = ("name", "author")
    list_filter = ("author",)


admin.site.register(BookType, BookTypeAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Book, BookAdmin)