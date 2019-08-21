from urllib.parse import parse_qsl


def parse(query):
    class ComponentName(str):
        def __new__(cls, *args, **kwargs):
            quoted = kwargs.pop('quoted', False)
            self = super().__new__(cls, *args, **kwargs)
            self.quoted = quoted
            return self

    def parse_brackets(s):
        def parse_component(s):
            ret = ''
            if s and s[0] == '"':
                idx = 1
                while idx < len(s):
                    if s[idx] == '"':
                        return ComponentName(ret, quoted=True), idx + 1
                    elif s[idx] == '\\':
                        if idx + 1 >= len(s):
                            raise ValueError()
                        ret += s[idx + 1]
                        idx += 1
                    else:
                        ret += s[idx]
                    idx += 1
                raise ValueError()
            else:
                idx = 0
                while idx < len(s):
                    if s[idx] in '"[]':
                        break
                    elif s[idx] == '\\':
                        if idx + 1 >= len(s):
                            raise ValueError()
                        ret += s[idx + 1]
                        idx += 1
                    else:
                        ret += s[idx]
                    idx += 1
                return ComponentName(ret, quoted=False), idx
                        
        ret = []
        component, startidx = parse_component(s)
        ret.append(component)
        while startidx < len(s):
            if s[startidx] != '[':
                raise ValueError('Syntax error')
            component, endidx = parse_component(s[startidx + 1:])
            endidx += startidx + 1
            if endidx >= len(s) or s[endidx] != ']':
                raise ValueError('Syntax error')

            ret.append(component)

            startidx = endidx + 1

        return ret

    def get_value_func(value_type_str):
        type_str = value_type_str
        if not type_str:
            return lambda x: x
        if type_str == 'u':
            return lambda x: None
        elif type_str == 'n':
            def number(x):
                if '.' in x:
                    return float(x)
                else:
                    return int(x)
            return number
        elif type_str == 'a':
            return lambda x: []
        elif type_str == 'o':
            return lambda x: {}
        elif type_str == 'b':
            def boolean(x):
                if x == 'true':
                    return True
                elif x == 'false':
                    return False
                return x
            return boolean
        return lambda x: x

    def parse_key(s):
        if not s or s[0] == '"':
            return '', parse_brackets(s)
        idx = s.find(':')
        if idx == -1:
            return '', parse_brackets(s)
        else:
            return s[:idx], parse_brackets(s[idx + 1:])

    def construct(query):
        # Two `ComponentName` objects that differs only in `quoted` field
        # are regarded as same key in dict.
        #
        # If query has both quoted and unquoted component of the same name,
        # we have to treat that component as quoted.

        quoted_keys = set()
        ret = {}
        for k, v in query:
            if len(k) == 0:
                ret.setdefault(None, []).append(v)
            else:
                ret.setdefault(k[0], []).append((k[1:], v))
                if k[0].quoted:
                    quoted_keys.add(k[0])
        for k, v in ret.items():
            if k in quoted_keys:
                k.quoted = True
            if k is not None:
                ret[k] = construct(v)
        return ret

    def simplify(query):
        key_none = query.get(None)
        # if query has `None` key
        if key_none is not None:
            if len(key_none) == 1: 
                return key_none[0]
            else:
                return key_none

        # If any of keys are quoted
        if any(k.quoted for k in query.keys()):
            return {k: simplify(v) for k, v in query.items()}

        key_empty = query.get('')
        if len(query) == 1 and key_empty is not None:
            # For example, goes here when `a[]=1&a[]=2` and not when `a[]=1&a[b]=2`

            if len(key_empty) == 1 and None in key_empty:
                # For example, goes here when `a[]=1` and not when `a[][b]=1`
                return key_empty[None]

        # if all keys are number
        if query and all(all(c in '1234567890' for c in k) for k in query.keys()):
            ret = [simplify(x[1]) for x in sorted(query.items(), key=lambda x: int(x[0]))]
            return ret

        return {k: simplify(v) for k, v in query.items()}

    if isinstance(query, bytes):
        query = str(query, encoding='utf-8')
    if isinstance(query, str):
        query = parse_qsl(query, keep_blank_values=True)

    def try_parse_key(k):
        try:
            return parse_key(k)
        except ValueError:
            return '', [k]
    query = [(try_parse_key(k), v) for k, v in query]

    top_level = next(((value_type_str, v) for (value_type_str, components), v in query
                      if value_type_str.startswith('^')), None)
    if top_level is not None:
        return get_value_func(top_level[0][1:])(top_level[1])

    query = ((get_value_func(value_type_str), components, v)
             for (value_type_str, components), v in query)
    query = ((components, value_func(v))
             for value_func, components, v in query)
    query = construct(query)
    return simplify(query)


if __name__ == '__main__':
    query = {
	'aaa': ['a0', 'a1'],
	'bbb[a]': ['ba'],
	'bbb[]': ['b '],
	'ccc[b]': ['cb0', 'cb1'],
	'ccc[a]': ['ca0', 'ca1'],
	'ccc[c][d]': ['ccd0', 'ccd1'],
	'ccc[c][e]': ['cce0', 'cce1'],
	'ddd[a][]': ['da0'],
	'ddd[b]': ['db'],
	'eee': ['e'],
	'fff[a][1]': ['fa1'],
	'fff[a][0]': ['fa0'],
	'fff[b][0][a]': ['fb0a'],
	'fff[b][1]': ['fb1'],
	'ggg[0][b]': ['g0b'],
	'ggg[0][a]': ['g0a'],
	'ggg[1][a]': ['g1a'],
	'ggg[1][b]': ['g1b'],
    }
    print(parse(query))
