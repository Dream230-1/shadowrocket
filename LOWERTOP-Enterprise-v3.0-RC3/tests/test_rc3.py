import unittest

from scripts.adblock_collision import domain_overlap, ip_overlap
from scripts.dns_audit import parse_bool, split_csv


class DnsAuditTests(unittest.TestCase):
    def test_parse_bool(self):
        self.assertIs(parse_bool('true'), True)
        self.assertIs(parse_bool('false'), False)
        self.assertIsNone(parse_bool('1'))

    def test_split_csv(self):
        self.assertEqual(split_csv('a,b, c'), ['a', 'b', 'c'])


class CollisionTests(unittest.TestCase):
    def test_exact_domain_suffix_overlap(self):
        hit, reason = domain_overlap(['DOMAIN', 'api.openai.com'], ['DOMAIN-SUFFIX', 'openai.com'])
        self.assertTrue(hit)
        self.assertEqual(reason, 'domain-in-suffix')

    def test_unrelated_domains(self):
        hit, reason = domain_overlap(['DOMAIN-SUFFIX', 'openai.com'], ['DOMAIN-KEYWORD', 'advert'])
        self.assertFalse(hit)
        self.assertIsNone(reason)

    def test_ip_overlap(self):
        hit, reason = ip_overlap(['IP-CIDR', '10.0.0.0/8'], ['IP-CIDR', '10.2.0.0/16'])
        self.assertTrue(hit)
        self.assertEqual(reason, 'cidr-overlap')


if __name__ == '__main__':
    unittest.main()
