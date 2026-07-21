import pytest
from dataclasses import dataclass
from mtress._helpers._util import enable_templating
from mtress.technologies import FuelCell, AFC
from mtress.technologies import Electrolyser, PEM_ELECTROLYSER


class TestTemplating:

    def test_template_success(self):

        # use FuelCell template with FuelCell class
        FuelCell(name="fc", nominal_power=100e3, template=AFC)
        # use Electrolyser template with Electrolyser class
        Electrolyser(
            name="elec", nominal_power=100e3, template=PEM_ELECTROLYSER
        )

    def test_template_fail(self):

        # use Electrolyser template with FuelCell class
        with pytest.raises(TypeError):
            FuelCell(name="fc", nominal_power=100e3, template=PEM_ELECTROLYSER)
        # use FuelCell template with Electrolyser class
        with pytest.raises(TypeError):
            Electrolyser(name="elec", nominal_power=100e3, template=AFC)

    def test_standard_use(self):

        # test normal use of templates

        @dataclass(frozen=True)
        class Template:
            a: float
            b: float

        @enable_templating(Template)
        def myfunction(a, b):
            return a + b

        # define template
        F1 = Template(a=1, b=2)
        # test it
        assert myfunction(template=F1) == 3
        # override template
        assert myfunction(a=2, template=F1) == 4

    def test_standard_use_extra_param(self):

        # test using templates together with additional parameters
        @dataclass(frozen=True)
        class Template:
            a: float
            c: float

        @enable_templating(Template)
        def myfunction(a, b, c):
            return a + b + c

        # define template
        F1 = Template(a=1, c=2)
        # test it
        assert myfunction(b=-1, template=F1) == 2
        # override template
        assert myfunction(a=2, b=2, template=F1) == 6

        with pytest.raises(TypeError):
            # only kwargs are allowed if templates are used
            assert myfunction(-1, template=F1) == 2

    def test_standard_use_default_param(self):

        # test using templates together with additional parameters
        @dataclass(frozen=True)
        class Template:
            a: float
            b: float

        @enable_templating(Template)
        def myfunction(a, b=3):
            return a + b

        # test without template and with default
        assert myfunction(a=2) == 5
        # test without template
        assert myfunction(a=2, b=4) == 6
        # define template
        F1 = Template(a=1, b=2)
        # test it (overrides default)
        assert myfunction(template=F1) == 3
        # override template for a and uses template for b
        assert myfunction(a=2, template=F1) == 4
        # overrides b but not a
        assert myfunction(b=3, template=F1) == 4
        # pointless but possible
        assert myfunction(a=2, b=4, template=F1) == 6

        with pytest.raises(TypeError):
            # only kwargs are allowed if templates are used
            assert myfunction(2, 4, template=F1) == 5

    def test_inheritance_methods(self):

        # test using templates with inheritance

        @dataclass(frozen=True)
        class TemplateF1:
            a: float
            b: float

        @enable_templating(TemplateF1)
        def myf1(a, b):
            return a + b

        @dataclass(frozen=True)
        class TemplateF2(TemplateF1):
            c: float
            d: float

        @enable_templating(TemplateF2)
        def myf2(c, d, **kwargs):
            return c + d + myf1(**kwargs)

        # test using args and kwargs
        assert myf2(3, 4, a=1, b=2) == 10
        # test using only kwargs
        assert myf2(c=3, d=4, a=1, b=2) == 10

        # # define template
        # F2 = TemplateF2(a=1, b=2, c=3, d=4)
        # # test using the template
        # assert myf2(template=F2) == 10
        # # test using kwargs and a template
        # assert myf2(c=4, d=5, template=F2) == 12

        # with pytest.raises(TypeError):
        #     # only kwargs are allowed if templates are used
        #     assert myf2(0, 1, template=F2) == 8

    def test_inheritance_classes(self):

        # test using templates with classes

        @dataclass(frozen=True)
        class TemplateF1:
            a: float
            b: float

        class class1:
            @enable_templating(TemplateF1)
            def __init__(self, a, b=-4):
                self.a = a
                self.b = b

            def myf1(self):
                return self.a + self.b

        @dataclass(frozen=True)
        class TemplateF2(TemplateF1):
            c: float
            d: float

        class class2(class1):

            @enable_templating(TemplateF2)
            def __init__(self, a, b, c, d):

                super().__init__(a, b)
                self.c = c
                self.d = d

            def myf2(self):
                return self.c + self.d + self.myf1()

        # test using args and kwargs
        I1 = class2(1, 2, c=3, d=4)
        assert I1.myf2() == 10
        # test using only kwargs
        I1 = class2(c=3, d=4, a=1, b=2)
        assert I1.myf2() == 10

        # define template
        F2 = TemplateF2(a=1, b=2, c=3, d=4)
        # test using the template
        I1 = class2(template=F2)
        assert I1.myf2() == 10
        # test using kwargs and a template
        I1 = class2(c=4, d=5, template=F2)
        assert I1.myf2() == 12

        with pytest.raises(TypeError):
            # only kwargs are allowed if templates are used
            I1 = class2(0, 1, template=F2)
            assert I1.myf2() == 8

    def test_inheritance_classes_alternative(self):

        # test using templates with classes

        @dataclass(frozen=True)
        class TemplateF1:
            a: float
            b: float

        class class1:
            @enable_templating(TemplateF1)
            def __init__(self, a, b=-4):
                self.a = a
                self.b = b

            def myf1(self):
                return self.a + self.b

        @dataclass(frozen=True)
        class TemplateF2(TemplateF1):
            c: float
            d: float

        class class2(class1):

            @enable_templating(TemplateF2)
            def __init__(self, c, d, **kwargs):

                super().__init__(**kwargs)
                self.c = c
                self.d = d

            def myf2(self):
                return self.c + self.d + self.myf1()

        # test using args and kwargs
        I1 = class2(3, 4, a=1, b=2)
        assert I1.myf2() == 10
        # test using only kwargs
        I1 = class2(c=3, d=4, a=1, b=2)
        assert I1.myf2() == 10
        # define template
        F2 = TemplateF2(a=1, b=2, c=3, d=4)
        # test using the template
        I1 = class2(template=F2)
        assert I1.myf2() == 10
        # test using kwargs and a template
        I1 = class2(c=4, d=5, template=F2)
        assert I1.myf2() == 12

        with pytest.raises(TypeError):
            # only kwargs are allowed if templates are used
            I1 = class2(0, 1, template=F2)
            assert I1.myf2() == 8
