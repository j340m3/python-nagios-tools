from unittest import TestCase, main
from nagios import Output, PerformanceData, gen_parser, parse, Threshold, Check, ReturnValue
from unittest.mock import patch
import sys


"""
class TestOutput(TestCase):
    def test_ok(self):
        o1 = Output()
        o1.service = "test_ok"
        o1.ok()
        self.fail()

    def test_warning(self):
        self.fail()

    def test_critical(self):
        self.fail()

    def test_unknown(self):
        self.fail()

    def test_format_output(self):
        self.fail()


class TestPerformanceData(TestCase):
    def test_format(self):
        pd1 = PerformanceData()
        pd1.label = "test_1"
        pd1.value = "56"
        print(pd1.format())

"""


class Test(TestCase):
    def test_gen_parser(self):
        """
        p = gen_parser("I don't need this.")
        print(p.parse_args("-w ~:10 -c ~:20".split()))
        print(p.parse_args("-w 10 -w 6 -w 4 -c 16 -c 10 -c 10".split()))
        print(p.parse_args("-w 10 6 4 -c 16 10 10".split()))
        """
        pass

    def test_parse2(self):
        t1 = list(parse(critical=[['~:20']], warning=[['~:10']]))
        t = t1[0]
        self.assertEqual(t.state(21), Threshold.CRITICAL)
        self.assertEqual(t.state(20), Threshold.WARNING)
        self.assertEqual(t.state(10), Threshold.OK)
        self.assertEqual(t.state(11), Threshold.WARNING)
        self.assertEqual(t.state(-1), Threshold.OK)

    def test_parse1(self):
        t1 = list(parse(critical=[['20']], warning=[['10']]))
        t = t1[0]
        self.assertEqual(t.state(21), Threshold.CRITICAL)
        self.assertEqual(t.state(20), Threshold.WARNING)
        self.assertEqual(t.state(10), Threshold.OK)
        self.assertEqual(t.state(11), Threshold.WARNING)
        self.assertEqual(t.state(-1), Threshold.CRITICAL)

    def test_parse3(self):
        t1 = list(parse(critical=[['20']], warning=[['10:']]))
        t = t1[0]
        self.assertEqual(t.state(21), Threshold.CRITICAL)
        self.assertEqual(t.state(20), Threshold.OK)
        self.assertEqual(t.state(10), Threshold.OK)
        self.assertEqual(t.state(9), Threshold.WARNING)
        self.assertEqual(t.state(-1), Threshold.CRITICAL)

    def test_parse4(self):
        t1 = list(parse(critical=[['1:']]))
        t = t1[0]
        self.assertEqual(t.state(0), Threshold.CRITICAL)
        self.assertEqual(t.state(1), Threshold.OK)

    def test_parse5(self):
        t1 = list(parse(critical=[['10']], warning=[['~:0']]))
        t = t1[0]
        self.assertEqual(t.state(11), Threshold.CRITICAL)
        self.assertEqual(t.state(10), Threshold.WARNING)
        self.assertEqual(t.state(0), Threshold.OK)
        self.assertEqual(t.state(1), Threshold.WARNING)
        self.assertEqual(t.state(-1), Threshold.CRITICAL)

    def test_parse6(self):
        t1 = list(parse(critical=[['5:6']]))
        t = t1[0]
        self.assertEqual(t.state(4), Threshold.CRITICAL)
        self.assertEqual(t.state(5), Threshold.OK)
        self.assertEqual(t.state(7), Threshold.CRITICAL)
        self.assertEqual(t.state(6), Threshold.OK)

    def test_parse7(self):
        t1 = list(parse(critical=[['@10:20']]))
        t = t1[0]
        self.assertEqual(t.state(9), Threshold.OK)
        self.assertEqual(t.state(10), Threshold.CRITICAL)
        self.assertEqual(t.state(20), Threshold.CRITICAL)
        self.assertEqual(t.state(21), Threshold.OK)


class TestCheck(TestCase):
    def test_adjust_parser(self):
        pass

    def test_integrate(self):
        class MyCheck(Check):
            def run(self, *args, **kwargs):
                self.output([ReturnValue(label="nope",value=-1),
                             ReturnValue(label="nö", value=11)], out_lines=["My result","On Multiple","Lines"])
        testargs = "prog -w ~:10 -c ~:20".split()
        with patch.object(sys, 'argv', testargs):
            try:
                c = MyCheck("MyTest")
                c.run()
            except SystemExit as e:
                if e.code != 1:
                    self.fail()


if __name__ == "__main__":
    main()
