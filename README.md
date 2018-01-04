# pearsql
Very simple sql query builder focusing on sqlite compatibility

For pretty much complete and rich library see [sqlbuilder](https://pypi.python.org/pypi/sqlbuilder)


## Example

```
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
```
