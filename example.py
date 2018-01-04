# coding=utf-8
from pearsql import D, Q, F

Q.USE_QUOTES = False

print(Q.select(D.book.as_("b")).distinct()
    .columns([D.book.title.as_("title"), D.author.name.as_("author_name")])
    .join(D.author.as_("a"), D.author.id == D.book.author_id)
    .where(D.author.gender != 1)
    .where(D.author.nation == "Germany")
    .having(F.count(D.author.publications) > 5)
    .groupby(D.book.category)
    .orderby(D.book.title)
    .limit(100)
    .offset(50)
    .build(True))

print(Q.update(D.author.as_("a"))
    .columns(D.author.name.set("Heinrich Böll"))
    .where(D.author.id == 27)
    .limit(1)
    .build(True))

print(Q.insert(D.author.as_("a"))
    .columns([D.author.name.set("Friedrich Schiller"), D.author.gender.set(F.default())])
    .build(True))

print(Q.delete(D.author.as_("a"))
    .where(D.author.id == 27)
    .build(True))
