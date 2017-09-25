
class Well:
    '''Cylindrical location for liquid storage'''
    def __init__(self, offset, max_volume, radius, depth):
        self._offset = offset
        self.max_volume = max_volume
        self.radius = radius
        self.depth = depth


class Trough:
    '''Rectangular Prism used for liquid storage'''
    def __init__(self, offset, max_volume, length, width, depth):
        self._offset = offset
        self.max_volume = max_volume
        self.length = length
        self.width = width
        self.depth = depth


class Deck:
    def __init__(self, offset):
        self._offset = offset
        self.slots = [[]] # nesting should be external


class Slot:
    def __init__(self, offset, name, length, width):
        self._offset = offset
        self.name = name
        self.length = length
        self.width = width


class Container:
    # NOTE: wells will not always be easily split into rows and columns
    def __init__(self, offset, numb_of_rows, numb_of_columns,
                 length, width, height, type):
        self._offset = offset
        self._numb_of_rows
        self._numb_of_columns
        self._wells = [[]]
        self.length = length
        self.width = width
        self.height = height
        self.type = type


    def __iter__(self):
        return self.wells

    @property
    def rows(self):
        pass

    @property
    def columns(self):
        return self._wells

    @property
    def wells(self):
        '''returns list of wells'''
        pass

    @property
    def shape(self):
        return (self._numb_of_rows, self._numb_of_columns)

    def add_well(self, well):
        numb_of_wells = len(self.wells)
        rows, columns = self.shape
        if numb_of_wells == rows * columns:
            raise RuntimeError("Can not add more wells to this container")
        else:
            row = numb_of_wells//rows
            column = numb_of_wells%columns
            self._wells[row][column] = well