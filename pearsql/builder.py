import sys
from six import with_metaclass

PY3 = sys.version_info[0] == 3

if PY3:
    __string_types = str,
else:
    __string_types = basestring,


# noinspection PyProtectedMember
def _enquote(query, s):
    if query._use_quotes:
        return '"%s"' % s
    else:
        return s


def _escape(query, obj):
    if isinstance(obj, __string_types):
        return "'%s'" % str(obj)
    elif isinstance(obj, SqlQuery):
        return "(" + obj.build(False, False) + ")"
    elif isinstance(obj, _SqlTable):
        alias = query.get_alias_for_table(obj)
        if alias:
            return "%s" % _enquote(query, alias)
        else:
            return obj.build(query)
    elif isinstance(obj, _SqlColumn):
        alias = query.get_alias_for_column(obj)
        if alias:
            return "%s" % _enquote(query, alias)
        else:
            alias = query.get_alias_for_table(obj.table)
            if alias:
                return "%s.%s" % (_enquote(query, alias), _enquote(query, obj.column))
            else:
                return obj.build(query)
    elif hasattr(obj, "build"):
        return obj.build(query)
    else:
        return str(obj)


class SqlException:
    def __init__(self, msg):
        self.message = msg


# Enums
class _SqlOperationType:
    UPDATE = 0
    INSERT = 1
    SELECT = 2
    DELETE = 3


class _SqlWhereConditionType:
    EQ = 0
    NEQ = 1
    GREATER = 2
    LESS = 3
    GEQ = 4
    LEQ = 5
    BETWEEN = 6
    LIKE = 7
    IN = 8
    EXISTS = 9
    AND = 10
    OR = 11
    NOT = 12


class _SqlFunctionType:
    MAX = 0
    MIN = 1
    AVG = 2
    COUNT = 3
    SUM = 4
    DEFAULT = 5


class _SqlOrderByType:
    ASC = 0
    DESC = 1


class _SqlJoinType:
    INNER = 0
    LEFT = 1
    RIGHT = 2
    FULL = 3


class _SqlJoin:
    def __init__(self, other_table, condition, type):
        self.other_table = other_table
        self.condition = condition
        self.type = type

    def build(self, query):
        postfix = "JOIN %s ON %s" % (self.other_table.build(query, True), self.condition.build(query))
        if self.type == _SqlJoinType.INNER:
            return "INNER " + postfix
        elif self.type == _SqlJoinType.LEFT:
            return "LEFT OUTER " + postfix
        elif self.type == _SqlJoinType.RIGHT:
            return "RIGHT OUTER " + postfix
        elif self.type == _SqlJoinType.FULL:
            return "FULL OUTER " + postfix
        else:
            raise SqlException("Unknown Join type")


class _SqlWhereStatement:
    def between(self, v1, v2):
        return _SqlWhereCondition(self, (v1, v2), _SqlWhereConditionType.BETWEEN)

    def like(self, s):
        return _SqlWhereCondition(self, s, _SqlWhereConditionType.LIKE)

    def in_(self, l):
        return _SqlWhereCondition(self, l, _SqlWhereConditionType.IN)

    def __invert__(self):
        return _SqlWhereCondition(self, None, _SqlWhereConditionType.NOT)

    def __eq__(self, other):
        return _SqlWhereCondition(self, other, _SqlWhereConditionType.EQ)

    def __ne__(self, other):
        return _SqlWhereCondition(self, other, _SqlWhereConditionType.NEQ)

    def __lt__(self, other):
        return _SqlWhereCondition(self, other, _SqlWhereConditionType.LESS)

    def __le__(self, other):
        return _SqlWhereCondition(self, other, _SqlWhereConditionType.LEQ)

    def __gt__(self, other):
        return _SqlWhereCondition(self, other, _SqlWhereConditionType.GREATER)

    def __ge__(self, other):
        return _SqlWhereCondition(self, other, _SqlWhereConditionType.GEQ)

    def __and__(self, other):
        return _SqlWhereCondition(self, other, _SqlWhereConditionType.AND)

    def __or__(self, other):
        return _SqlWhereCondition(self, other, _SqlWhereConditionType.OR)


class _SqlWhereCondition(_SqlWhereStatement):
    def __init__(self, op1, op2, type):
        self._op1 = op1
        self._op2 = op2
        self._type = type

    def build(self, query):
        if self._type == _SqlWhereConditionType.EQ:
            return "(%s = %s)" % (_escape(query, self._op1), _escape(query, self._op2))
        elif self._type == _SqlWhereConditionType.NEQ:
            return "(%s <> %s)" % (_escape(query, self._op1), _escape(query, self._op2))
        elif self._type == _SqlWhereConditionType.GREATER:
            return "(%s > %s)" % (_escape(query, self._op1), _escape(query, self._op2))
        elif self._type == _SqlWhereConditionType.LESS:
            return "(%s < %s)" % (_escape(query, self._op1), _escape(query, self._op2))
        elif self._type == _SqlWhereConditionType.GEQ:
            return "(%s >= %s)" % (_escape(query, self._op1), _escape(query, self._op2))
        elif self._type == _SqlWhereConditionType.LEQ:
            return "(%s <= %s)" % (_escape(query, self._op1), _escape(query, self._op2))
        elif self._type == _SqlWhereConditionType.LIKE:
            return "(%s LIKE %s)" % (_escape(query, self._op1), _escape(query, self._op2))
        elif self._type == _SqlWhereConditionType.BETWEEN:
            return "(%s BETWEEN %s AND %s)" % (
                _escape(query, self._op1), _escape(query, self._op2[0]), _escape(query, self._op2[1]))
        elif self._type == _SqlWhereConditionType.IN:
            if isinstance(self._op2, SqlQuery) or isinstance(self._op2, _SqlTable):
                return "(%s IN %s)" % (_escape(query, self._op1), _escape(query, self._op2))
            else:
                return "(%s IN (%s))" % (_escape(query, self._op1), ', '.join(_escape(query, e) for e in self._op2))
        elif self._type == _SqlWhereConditionType.EXISTS:
            return "(EXISTS %s)" % (_escape(query, self._op1))
        elif self._type == _SqlWhereConditionType.AND:
            return "(%s AND %s)" % (_escape(query, self._op1), _escape(query, self._op2))
        elif self._type == _SqlWhereConditionType.OR:
            return "(%s OR %s)" % (_escape(query, self._op1), _escape(query, self._op2))
        elif self._type == _SqlWhereConditionType.NOT:
            return "(NOT %s)" % (_escape(query, self._op1))
        else:
            raise SqlException("Unknown where condition type: %s" % str(self._type))


class SqlFunction(_SqlWhereStatement):
    def __init__(self, op, type):
        self._op = op
        self._type = type

    def build(self, query):
        if self._type == _SqlFunctionType.MAX:
            return "MAX(%s)" % _escape(query, self._op)
        elif self._type == _SqlFunctionType.MIN:
            return "MIN(%s)" % _escape(query, self._op)
        elif self._type == _SqlFunctionType.AVG:
            return "AVG(%s)" % _escape(query, self._op)
        elif self._type == _SqlFunctionType.COUNT:
            return "COUNT(%s)" % _escape(query, self._op)
        elif self._type == _SqlFunctionType.SUM:
            return "SUM(%s)" % _escape(query, self._op)
        elif self._type == _SqlFunctionType.DEFAULT:
            return "DEFAULT"
        else:
            raise SqlException("Unknown function type: %s" % str(self._type))

    @staticmethod
    def max(op):
        return SqlFunction(op, _SqlFunctionType.MAX)

    @staticmethod
    def min(op):
        return SqlFunction(op, _SqlFunctionType.MIN)

    @staticmethod
    def avg(op):
        return SqlFunction(op, _SqlFunctionType.AVG)

    @staticmethod
    def count(op):
        return SqlFunction(op, _SqlFunctionType.COUNT)

    @staticmethod
    def sum(op):
        return SqlFunction(op, _SqlFunctionType.SUM)

    @staticmethod
    def default():
        return SqlFunction(None, _SqlFunctionType.DEFAULT)


class _SqlColumn(_SqlWhereStatement):
    def __init__(self, table, column):
        self.table = table
        self.column = column
        self.alias = None
        self.value = None

    def build(self, query, with_as=False):
        if with_as and self.alias:
            return "%s.%s AS %s" % (
            _escape(query, self.table), _enquote(query, self.column), _enquote(query, self.alias))
        else:
            return "%s.%s" % (_escape(query, self.table), _enquote(query, self.column))

    def build_value(self, query):
        if self.value is None:
            if not query._ignore_none:
                raise SqlException("None value given")
            else:
                return "NULL"
        else:
            return _escape(query, self.value)

    def as_(self, alias):
        self.alias = alias
        return self

    def set(self, value):
        self.value = value
        return self


class _SqlTable:
    def __init__(self, name):
        self._name = name
        self._alias = None

    def build(self, query, with_as=False):
        if with_as and self._alias:
            return "%s AS %s" % (_enquote(query, self._name), _enquote(query, self._alias))
        else:
            return "%s" % _enquote(query, self._name)

    def as_(self, alias):
        self._alias = alias
        return self

    def __getattr__(self, item):
        return _SqlColumn(self, item)


class _SqlDatabase(type):
    def __getattr__(self, item):
        return _SqlTable(item)


class SqlDatabase(with_metaclass(_SqlDatabase)):
    pass


class SqlQuery:
    # Some default values
    IGNORE_NONE = False
    USE_QUOTES = True
    USE_ALIASES = True

    # TODO: Multiple equal columns??
    def __init__(self, operation):
        self._operation = operation
        self._tables = []
        self._columns = []
        self._wheres = []
        self._havings = []
        self._orderby_table = {}
        self._groupby_list = []
        self._joins = []
        self._last_column = None
        self._last_orderby = None
        self._union = None

        self._select_distinct = False
        self._limit = 0
        self._offset = 0

        self._ignore_none = SqlQuery.IGNORE_NONE
        self._use_quotes = SqlQuery.USE_QUOTES
        self._use_aliases = SqlQuery.USE_ALIASES

    # First step: Operator
    @staticmethod
    def select(*tables):
        return SqlQuery.__start_operation(tables, _SqlOperationType.SELECT)

    @staticmethod
    def insert(*tables):
        return SqlQuery.__start_operation(tables, _SqlOperationType.INSERT)

    @staticmethod
    def update(*tables):
        return SqlQuery.__start_operation(tables, _SqlOperationType.UPDATE)

    @staticmethod
    def delete(*tables):
        return SqlQuery.__start_operation(tables, _SqlOperationType.DELETE)

    @staticmethod
    def __start_operation(tables, operation):
        query = SqlQuery(operation)
        query._tables.extend(tables)
        return query

    # Flags
    def distinct(self):
        if self._operation != _SqlOperationType.SELECT:
            raise SqlException("Need Select operator for distinct")

        self._select_distinct = True
        return self

    def limit(self, count):
        self._limit = count
        return self

    def offset(self, count):
        self._offset = count
        return self

    def ignore_none(self, b=True):
        self._ignore_none = b
        return self

    def use_quotes(self, b=True):
        self._use_quotes = b
        return self

    def use_aliases(self, b=True):
        self._use_aliases = b
        return self

    # (Optional)
    def tables(self, *l):
        self._tables.extend(l)
        return self

    # Columns
    def columns(self, *l):
        self._columns.extend(l)
        return self

    # Where
    def where(self, *condition):
        self._wheres.extend(condition)
        return self

    # Having
    def having(self, *condition):
        self._havings.extend(condition)
        return self

    # Order By
    # TODO: Position of queue element important?
    def orderby(self, *columns):
        if self._operation != _SqlOperationType.SELECT:
            raise SqlException("Need Select operator for orderby")

        for c in columns:
            self._orderby_table[str(c)] = (_SqlOrderByType.ASC, c)
            self._last_orderby = c
        return self

    def asc(self):
        if self._operation != _SqlOperationType.SELECT:
            raise SqlException("Need Select operator for asc")
        if self._last_orderby is None:
            raise SqlException("No previous orderby")

        self._orderby_table[str(self._last_orderby)] = (_SqlOrderByType.ASC, self._last_orderby)
        return self

    def desc(self):
        if self._operation != _SqlOperationType.SELECT:
            raise SqlException("Need Select operator for desc")
        if self._last_orderby is None:
            raise SqlException("No previous orderby")

        self._orderby_table[str(self._last_orderby)] = (_SqlOrderByType.DESC, self._last_orderby)
        return self

    # Group By
    def groupby(self, *columns):
        if self._operation != _SqlOperationType.SELECT:
            raise SqlException("Need Select operator for groupby")

        self._groupby_list.extend(columns)
        return self

    # Joins
    def __add_join(self, table2, condition, type):
        if self._operation != _SqlOperationType.SELECT:
            raise SqlException("Need Select operator for joins")

        self._joins.append(_SqlJoin(table2, condition, type))
        return self

    def join(self, table2, condition):
        return self.__add_join(table2, condition, _SqlJoinType.INNER)

    def left_join(self, table2, condition):
        return self.__add_join(table2, condition, _SqlJoinType.LEFT)

    def right_join(self, table2, condition):
        return self.__add_join(table2, condition, _SqlJoinType.RIGHT)

    def full_join(self, table2, condition):
        return self.__add_join(table2, condition, _SqlJoinType.FULL)

    # Union
    def union(self, other_query):
        if self._operation != _SqlOperationType.SELECT:
            raise SqlException("Need Select operator for unions")
        # noinspection PyProtectedMember
        if other_query._operation != _SqlOperationType.SELECT:
            raise SqlException("Other query needs to be of Select type")
        if self._union is not None:
            raise SqlException("Union partner already set")

        self._union = other_query
        return self

    def __add__(self, other):
        return self.union(other)

    # Final step:)
    # noinspection PyProtectedMember
    def get_alias_for_table(self, table):
        if self._use_aliases:
            for ot in self._tables:
                if ot._name == table._name:
                    return ot._alias
            for j in self._joins:
                if j.other_table._name == table._name:
                    return j.other_table._alias
        return None

    # noinspection PyProtectedMember
    def get_alias_for_column(self, c):
        if self._use_aliases:
            for oc in self._columns:
                if oc.table._name == c.table._name and oc.column == c.column:
                    return oc.alias
        return None

    def _build_select_columns(self):
        if len(self._columns) == 0:
            return "*"
        else:
            return ", ".join(e.build(self, True) for e in self._columns)

    def _build_insert_columns(self):
        return ", ".join(_enquote(self, e.column) for e in self._columns)

    def _build_tables(self):
        if not self._tables:
            raise SqlException("No table given")

        q = ", ".join(e.build(self, self._use_aliases) for e in self._tables)
        return q

    def _build_where(self):
        return "WHERE " + " AND ".join(cond.build(self) for cond in self._wheres)

    def _build_having(self):
        return "HAVING " + " AND ".join(cond.build(self) for cond in self._havings)

    def _build_groupby(self):
        return "GROUP BY " + ", ".join(_escape(self, c) for c in self._groupby_list)

    def _build_orderby_entity(self, key_c):
        if self._orderby_table[key_c][0] == _SqlOrderByType.ASC:
            return _escape(self, self._orderby_table[key_c][1]) + " ASC"
        else:
            return _escape(self, self._orderby_table[key_c][1]) + " DESC"

    def _build_orderby(self):
        return "ORDER BY " + ", ".join(self._build_orderby_entity(c) for c in self._orderby_table)

    def _build_joins(self):
        return " ".join(j.build(self) for j in self._joins)

    def _build_values(self):
        return "(" + ", ".join(e.build_value(self) for e in self._columns) + ")"

    def build(self, beautiful=False, complete=True):
        if beautiful:
            sep = "\n"
        else:
            sep = " "

        q = ""
        if self._operation == _SqlOperationType.SELECT:
            q = "SELECT"
            if self._select_distinct:
                q += " DISTINCT"
            q += sep

            q += self._build_select_columns() + sep
            q += "FROM " + self._build_tables() + sep
            if self._joins:
                q += self._build_joins() + sep
            if self._wheres:
                q += self._build_where() + sep
            if self._havings:
                q += self._build_having() + sep
            if self._groupby_list:
                q += self._build_groupby() + sep
            if self._orderby_table:
                q += self._build_orderby() + sep
            if self._limit > 0:
                q += "LIMIT " + str(self._limit) + sep
            if self._offset > 0:
                q += "OFFSET " + str(self._offset) + sep
            if self._union:
                q += "UNION " + self._union.build(beautiful, False)
        elif self._operation == _SqlOperationType.INSERT:
            self._use_aliases = False  # No aliases allowed
            q = "INSERT INTO "
            q += self._build_tables() + " "
            if self._columns:
                q += "(" + self._build_insert_columns() + ")" + sep
                q += "VALUES " + self._build_values() + sep
            else:
                q += "DEFAULT VALUES" + sep
        elif self._operation == _SqlOperationType.UPDATE:
            q = "UPDATE "
            q += self._build_tables() + sep
            q += "SET " + self._build_values() + sep
            if self._joins:
                q += self._build_joins() + sep
            if self._wheres:
                q += self._build_where() + sep
            if self._havings:
                q += self._build_having() + sep
            if self._orderby_table:
                q += self._build_orderby() + sep
            if self._limit > 0:
                q += "LIMIT " + str(self._limit) + sep
            if self._offset > 0:
                q += "OFFSET " + str(self._offset) + sep
        elif self._operation == _SqlOperationType.DELETE:
            self._use_aliases = False  # No aliases allowed
            q = "DELETE FROM " + sep
            q += self._build_tables() + sep
            if self._wheres:
                q += self._build_where() + sep
            if self._orderby_table:
                q += self._build_orderby() + sep
            if self._limit > 0:
                q += "LIMIT " + str(self._limit) + sep
            if self._offset > 0:
                q += "OFFSET " + str(self._offset) + sep

        if complete:
            return q + ";"
        else:
            return q
