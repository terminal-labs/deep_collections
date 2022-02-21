def deep_collection(obj):
    class DeepCollection(type(obj)):
        def __getitem__(self, key):
            print(key)
            try:
                iter(key)
            except TypeError:
                item = super().__getitem__(key)

                try:
                    iter(item)
                except TypeError:
                    return item

                return deep_collection(item)

            current_step = key[0]
            next_key = key[1:]

            item = super().__getitem__(current_step)

            if next_key:
                return deep_collection(item)[next_key]
            return item

    iter(obj)

    return DeepCollection(obj)
