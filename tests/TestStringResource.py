from unittest import TestCase

from mcscript.lang.resource.StringResource import StringResource


class TestStringResource(TestCase):
    def testFormatter(self):
        resource = StringResource("Hello, $world! My name is $name and $number + $number = $result", True)
        self.assertEqual(resource.format(world="World", result=2, name="David", number=1).value,
                         "Hello, World! My name is David and 1 + 1 = 2")
