cat query | sed  s/'?'/placeholder/g | sed ':a;N;$!ba;s/\n/ /g' | /tmp/queryparser
