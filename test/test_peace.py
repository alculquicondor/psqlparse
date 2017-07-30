# -*- coding: utf-8 -*-
# :Project:   psqlparse -- Tests for the pretty indenter
# :Created:   ven 28 lug 2017 13:42:05 CEST
# :Author:    Lele Gaifax <lele@metapensiero.it>
# :License:   BSD
# :Copyright: © 2017 Lele Gaifax
#

import pytest

from psqlparse.parser import parse_dict
from psqlparse.peace import PrettyPrinter


def remove_location(d):
    "Drop the node location, pointless for comparison between raw and pretty printed nodes."

    if isinstance(d, list):
        for v in d:
            if v:
                remove_location(v)
    else:
        d.pop('location', None)
        for v in d.values():
            if v and isinstance(v, (dict, list)):
                remove_location(v)


SQLS = """
SELECT pc.id as x, common.func(pc.name, ' '), 123 FROM ns.table
;;
SELECT 'accbf276-705b-11e7-b8e4-0242ac120002'::UUID as "X"
;;
SELECT x.id, (select count(*) FROM sometable as y where y.id = x.id) count
from firsttable as x
;;
select id, count(*) FROM sometable GROUP BY id
order by id desc nulls last;
;;
SELECT id, count(*) FROM sometable GROUP BY id having count(*) > 2
order by count(*) using @> nulls first;
;;
SELECT DISTINCT ON (pc.id) pc.id as x, pc.foo, pc.bar, other.some
FROM ns.table AS pc, ns.other as other
WHERE pc.id < 10 and pc.foo = 'a'
  and (pc.foo = 'b' or pc.foo = 'c'
       and (x = 1 or x = 2));
;;
select a,b from sometable
union
select c,d from othertable
;;
select a,b from sometable
union all
select c,d from othertable
;;
select a,b from sometable
except
select c,d from othertable
;;
select a,b from sometable
intersect all
select c,d from othertable
;;
SELECT count(distinct a) from sometable
;;
SELECT array_agg(a ORDER BY b DESC) FROM sometable
;;
SELECT count(*) AS a, count(*) FILTER (WHERE i < 5 or i > 10) AS b
FROM sometable
;;
SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY income) FROM households
;;
SELECT depname, empno, salary, avg(salary) OVER (PARTITION BY depname)
FROM empsalary
;;
SELECT depname, empno, salary,
       rank() OVER (PARTITION BY depname ORDER BY salary DESC)
FROM empsalary
;;
SELECT salary, sum(salary) OVER () FROM empsalary
;;
SELECT salary, sum(salary) OVER (ORDER BY salary) FROM empsalary
;;
SELECT depname, empno, salary, enroll_date,
      rank() OVER (PARTITION BY depname ORDER BY salary DESC, empno) AS pos
FROM empsalary
;;
SELECT sum(salary) OVER "X", avg(salary) OVER y
FROM empsalary
WINDOW "X" AS (PARTITION BY depname ORDER BY salary DESC),
       y as (order by salary)
;;
select a.id, b.value
from sometable a join othertable b on b.id = a.id
;;
select a.id, b.value
from sometable a natural join othertable b
;;
select a.id, b.value
from sometable a join othertable b using (id)
;;
select name from sometable limit 2 offset 3
;;
select name from sometable offset 3 fetch next 2 rows only
;;
SELECT m.* FROM mytable m FOR UPDATE
;;
SELECT m.* FROM mytable m FOR SHARE of m nowait
;;
select case a.value when 0 then '1' else '2' end from sometable a
;;
select case when a.value = 0 then '1' else '2' end from sometable a
;;
SELECT * FROM unnest(ARRAY['a','b','c','d','e','f']) WITH ORDINALITY
;;
SELECT * FROM (VALUES (1, 'one'), (2, 'two')) AS t (num, letter)
;;
SELECT m.name AS mname, pname
FROM manufacturers m, LATERAL get_product_names(m.id) pname
;;
SELECT m.name AS mname, pname
FROM manufacturers m LEFT JOIN LATERAL get_product_names(m.id) pname ON true
;;
SELECT m.name FROM manufacturers m WHERE m.deliver_date = CURRENT_DATE
;;
WITH t AS (
    SELECT random() as x FROM generate_series(1, 3)
  )
SELECT * FROM t
UNION ALL
SELECT * FROM t
;;
WITH RECURSIVE employee_recursive(distance, employee_name, manager_name) AS (
    SELECT 1, employee_name, manager_name
    FROM employee
    WHERE manager_name = 'Mary'
  UNION ALL
    SELECT er.distance + 1, e.employee_name, e.manager_name
    FROM employee_recursive er, employee e
    WHERE er.employee_name = e.manager_name
  )
SELECT distance, employee_name FROM employee_recursive
;;
update sometable set value = 'foo' where id = 'bar'
"""


@pytest.mark.parametrize('sql', (sql.strip() for sql in SQLS.split('\n;;\n')))
def test_peace(sql):
    orig_ast = parse_dict(sql)
    remove_location(orig_ast)
    printer = PrettyPrinter()
    indented = printer(sql)
    try:
        indented_ast = parse_dict(indented)
    except:
        raise RuntimeError("Could not reparse %r" % indented)
    remove_location(indented_ast)
    if 'CURRENT_DATE' in indented:
        print()
        print(indented)
    assert orig_ast == indented_ast, "%r != %r" % (sql, indented)
