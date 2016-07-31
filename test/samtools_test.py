#pylint: disable=invalid-name, too-few-public-methods, too-many-public-methods
#pylint: disable=protected-access, missing-docstring, too-many-locals
#pylint: disable=too-many-arguments,deprecated-method
from __future__ import print_function, absolute_import, division
import os
import pysam
from testfixtures.tempdirectory import TempDirectory

import test.utils_test as utils_test
from connor.samtools import BamFlag
from connor.samtools import ConnorAlign
import connor.samtools as samtools


def mock_align(**kwargs):
    a = pysam.AlignedSegment()
    a.query_name = "align1"
    a.flag = 99
    a.reference_id = 0
    a.reference_start = 32
    a.mapping_quality = 20
    a.cigar = ((0,3), (2,1), (0,1))
    a.next_reference_id = 0
    a.next_reference_start=199
    a.template_length=167
    #query_qualities must be set after query_sequence
    a.query_sequence=kwargs.pop('query_sequence', 'AGCTTAG')
    for (key, value) in kwargs.items():
        setattr(a, key, value)
    return a

def _create_file(path, filename, contents):
    filename = os.path.join(path, filename)
    with open(filename, 'wt') as new_file:
        new_file.write(contents)
        new_file.flush()
    return filename

def create_bam(path, filename, sam_contents, index=True):
    sam_filename = _create_file(path, filename, sam_contents)
    bam_filename = sam_filename.replace(".sam", ".bam")
    pysam_bam_from_sam(sam_filename, bam_filename, index)
    return bam_filename

def pysam_bam_from_sam(sam_filename, bam_filename, index=True):
    infile = samtools.alignment_file(sam_filename, "r")
    outfile = samtools.alignment_file(bam_filename, "wb", template=infile)
    for s in infile:
        outfile.write(s)
    infile.close()
    outfile.close()
    if index:
        samtools.index(bam_filename)

def pysam_alignments_from_bam(bam_filename):
    infile = samtools.alignment_file(bam_filename, "rb")
    aligned_segments = [s for s in infile]
    infile.close()
    return aligned_segments


class ConnorAlignTest(utils_test.BaseConnorTestCase):
    def test_gettersPassthroughToPysamAlignSegment(self):
        pysam_align = mock_align(query_name="queryname_1",
                            flag=99,
                            reference_id=3,
                            reference_start=142,
                            mapping_quality=20,
                            cigarstring="8M",
                            next_reference_id=4,
                            next_reference_start=242,
                            template_length=100,
                            query_sequence="ACGTACGT",
                            query_qualities=[20]*8,
                            )
        connor_align = ConnorAlign(pysam_align)

        self.assertEqual('queryname_1', connor_align.query_name)
        self.assertEqual(99, connor_align.flag)
        self.assertEqual(3, connor_align.reference_id)
        self.assertEqual(142, connor_align.reference_start)
        self.assertEqual(20, connor_align.mapping_quality)
        self.assertEqual('8M', connor_align.cigarstring)
        self.assertEqual(242, connor_align.next_reference_start)
        self.assertEqual(100, connor_align.template_length)
        self.assertEqual(b'ACGTACGT', connor_align.query_sequence)
        self.assertEqual([20] * 8, connor_align.query_qualities)
        self.assertEqual(150, connor_align.reference_end)

    def test_settersPassthroughToPysamAlignSegment(self):
        pysam_align = mock_align(query_name="queryname_1",
                            flag=99,
                            reference_id=3,
                            reference_start=142,
                            mapping_quality=20,
                            cigarstring="8M",
                            next_reference_id=4,
                            next_reference_start=242,
                            template_length=100,
                            query_sequence="ACGTACGT",
                            query_qualities=[20]*8,
                            )
        connor_align = ConnorAlign(pysam_align)


        connor_align.query_name = 'queryname_11'
        connor_align.flag = 147
        connor_align.reference_id = 13
        connor_align.reference_start = 1142
        connor_align.mapping_quality = 120
        connor_align.cigarstring = "2S8M"
        connor_align.next_reference_id = 14
        connor_align.next_reference_start = 1242
        connor_align.template_length = 1100
        connor_align.query_sequence = "TTACGTACGT"
        connor_align.query_qualities = [20]*10

        self.assertEqual('queryname_11', pysam_align.query_name)
        self.assertEqual(147, pysam_align.flag)
        self.assertEqual(13, pysam_align.reference_id)
        self.assertEqual(1142, pysam_align.reference_start)
        self.assertEqual(120, pysam_align.mapping_quality)
        self.assertEqual('2S8M', pysam_align.cigarstring)
        self.assertEqual(1242, pysam_align.next_reference_start)
        self.assertEqual(1100, pysam_align.template_length)
        self.assertEqual(b'TTACGTACGT', pysam_align.query_sequence)
        self.assertEqual([20] * 10, pysam_align.query_qualities)
        self.assertEqual(1150, pysam_align.reference_end)

    def test_filter(self):
        pysam_align = mock_align(query_name="queryname_1",
                            flag=99,
                            reference_id=3,
                            reference_start=142,
                            mapping_quality=20,
                            cigarstring="8M",
                            next_reference_id=4,
                            next_reference_start=242,
                            template_length=100,
                            query_sequence="ACGTACGT",
                            query_qualities=[20]*8,
                            )
        connor_align = ConnorAlign(pysam_align)

        self.assertEqual(None, connor_align.filter)
        connor_align.filter = 'foo'
        self.assertEqual('foo', connor_align.filter)


class SamtoolsTest(utils_test.BaseConnorTestCase):
    def test_sort_and_index_bam(self):
        sam_contents = \
'''@HD|VN:1.4|GO:none|SO:coordinate
@SQ|SN:chr10|LN:135534747
readNameB1|147|chr10|400|0|5M|=|200|100|CCCCC|>>>>>
readNameA1|147|chr10|300|0|5M|=|100|100|AAAAA|>>>>>
readNameA1|99|chr10|100|0|5M|=|300|200|AAAAA|>>>>>
readNameB1|99|chr10|200|0|5M|=|400|200|CCCCC|>>>>>
readNameA2|147|chr10|300|0|5M|=|100|100|AAAAA|>>>>>
readNameA2|99|chr10|100|0|5M|=|300|200|AAAAA|>>>>>
'''.replace("|", "\t")

        with TempDirectory() as tmp_dir:
            bam = create_bam(tmp_dir.path,
                             "input.sam",
                             sam_contents,
                              index=False)
            samtools.sort_and_index_bam(bam)
            alignments = samtools.alignment_file(bam, "rb").fetch()
            aligns = [(a.query_name, a.reference_start + 1) for a in alignments]
            self.assertEquals(6, len(aligns))
            self.assertEquals([("readNameA1", 100),
                               ("readNameA2", 100),
                               ("readNameB1", 200),
                               ("readNameA1", 300),
                               ("readNameA2", 300),
                               ("readNameB1", 400)],
                              aligns)

            original_dir = os.getcwd()
            try:
                os.chdir(tmp_dir.path)
                os.mkdir("tmp")
                bam = create_bam(os.path.join(tmp_dir.path, "tmp"),
                                 "input.sam",
                                 sam_contents,
                                 index=False)
                bam_filename = os.path.basename(bam)

                samtools.sort_and_index_bam(os.path.join("tmp", bam_filename))

                alignments = samtools.alignment_file(bam, "rb").fetch()
                aligns = [(a.query_name,
                           a.reference_start + 1) for a in alignments]
                self.assertEquals(6, len(aligns))
                self.assertEquals([("readNameA1", 100),
                                   ("readNameA2", 100),
                                   ("readNameB1", 200),
                                   ("readNameA1", 300),
                                   ("readNameA2", 300),
                                   ("readNameB1", 400)],
                                  aligns)
            finally:
                os.chdir(original_dir)

    def test_filter_alignments_passthorughIncludedAligns(self):
        align1 = mock_align(query_name="align1")
        base = [align1]

        filtered_aligns = [x for x in samtools.filter_alignments(base)]

        self.assertEqual(base, filtered_aligns)

    def test_filter_alignments_excludesUnpairedAligns(self):
        flag = 99
        align1 = mock_align(query_name="align1", flag=flag)
        align2 = mock_align(query_name="align2", flag=flag ^ BamFlag.PROPER_PAIR)
        align3 = mock_align(query_name="align3", flag=flag)
        base = [align1, align2, align3]

        actual_names = [x.query_name for x in samtools.filter_alignments(base)]

        self.assertEqual(["align1", "align3"], actual_names)

    def test_filter_alignments_excludesSecondaryAligns(self):
        flag = 99
        align1 = mock_align(query_name="align1", flag=flag)
        align2 = mock_align(query_name="align2", flag=flag | BamFlag.SECONDARY)
        align3 = mock_align(query_name="align3", flag=flag)
        base = [align1, align2, align3]

        actual_names = [x.query_name for x in samtools.filter_alignments(base)]

        self.assertEqual(["align1", "align3"], actual_names)

    def test_filter_alignments_excludesQCFails(self):
        flag = 99
        align1 = mock_align(query_name="align1", flag=flag)
        align2 = mock_align(query_name="align2", flag=flag | BamFlag.QCFAIL)
        align3 = mock_align(query_name="align3", flag=flag)
        base = [align1, align2, align3]

        actual_names = [x.query_name for x in samtools.filter_alignments(base)]

        self.assertEqual(["align1", "align3"], actual_names)

    def test_filter_alignments_excludesMapq0(self):
        align1 = mock_align(query_name="align1", mapping_quality=1)
        align2 = mock_align(query_name="align2", mapping_quality=0)
        align3 = mock_align(query_name="align3", mapping_quality=1)
        base = [align1, align2, align3]

        actual_names = [x.query_name for x in samtools.filter_alignments(base)]

        self.assertEqual(["align1", "align3"], actual_names)

    def test_filter_alignments_excludesCigarUnavailable(self):
        align1 = mock_align(query_name="align1", cigarstring="6M")
        align2 = mock_align(query_name="align2", cigarstring="*")
        align3 = mock_align(query_name="align3", cigarstring="6M")
        base = [align1, align2, align3]

        actual_names = [x.query_name for x in samtools.filter_alignments(base)]

        self.assertEqual(["align1", "align3"], actual_names)

    def test_filter_alignments_logsFilterStats(self):
        align1 = mock_align(query_name="align1", cigarstring="6M")
        align2 = mock_align(query_name="align2", mapping_quality=0)
        align3 = mock_align(query_name="align2", cigarstring="*", mapping_quality=0)
        align4 = mock_align(query_name="align3", cigarstring="6M")
        base = [align1, align2, align3, align4]

        log = utils_test.MockLogger()
        for dummy in samtools.filter_alignments(base, log):
            pass

        self.assertEqual(log._log_calls['DEBUG'][0],
                         r'filter_align|2/4 (50.00%) alignments passed '
                         r'filtering')
        self.assertEqual(log._log_calls['DEBUG'][1],
                        (r'filter_align|2/4 (50.00%) alignments failed '
                         r'filtering and will be excluded (see log file)'))
        self.assertRegexpMatches(log._log_calls['DEBUG'][2],
                                 '1 alignment.*cigar unavail.*mapping quality')
        self.assertRegexpMatches(log._log_calls['DEBUG'][3],
                                 '1 alignment.*mapping quality')
        self.assertEqual(4, len(log._log_calls['DEBUG']))


class AlignWriterTest(utils_test.BaseConnorTestCase):
    def test_init_defaultToNoTags(self):
        with TempDirectory() as tmp_dir:
            bam_path = os.path.join(tmp_dir.path, "destination.bam")
            header = { 'HD': {'VN': '1.0'},
                      'SQ': [{'LN': 1575, 'SN': 'chr1'},
                             {'LN': 1584, 'SN': 'chr2'}] }
            writer = samtools.AlignWriter(header, bam_path)
            writer.close()
        self.assertEqual({}, writer._tags)

    def test_write(self):
        with TempDirectory() as tmp_dir:
            bam_path = os.path.join(tmp_dir.path, "destination.bam")
            header = { 'HD': {'VN': '1.0'},
                      'SQ': [{'LN': 1575, 'SN': 'chr1'},
                             {'LN': 1584, 'SN': 'chr2'}] }
            align1 = ConnorAlign(mock_align(query_name="align1"))
            align2 = ConnorAlign(mock_align(query_name="align2"))
            align3 = ConnorAlign(mock_align(query_name="align3"))
            family = None
            writer = samtools.AlignWriter(header, bam_path)

            writer.write(family, align1)
            writer.write(family, align2)
            writer.write(family, align3)
            writer.close()
            samtools.index(bam_path)

            bamfile = samtools.alignment_file(bam_path, 'rb')
            actual_query_names = [align.query_name for align in bamfile.fetch()]
            bamfile.close()

        self.assertEqual(['align1', 'align2', 'align3'], actual_query_names)

    def test_write_addsAlignTags(self):
        with TempDirectory() as tmp_dir:
            bam_path = os.path.join(tmp_dir.path, 'destination.bam')
            header = { 'HD': {'VN': '1.0'},
                      'SQ': [{'LN': 1575, 'SN': 'chr1'},
                             {'LN': 1584, 'SN': 'chr2'}] }
            align1 = ConnorAlign(mock_align(query_name='align1'))
            align2 = ConnorAlign(mock_align(query_name='align2'))
            align3 = ConnorAlign(mock_align(query_name='align3'))

            tags = {'X1' : ('Z', lambda family, align: family, ''),
                    'X2' : ('Z', lambda family, align: align.query_name, '')}
            writer = samtools.AlignWriter(header, bam_path, tags)

            writer.write('familyA', align1)
            writer.write('familyB', align2)
            writer.write('familyC', align3)
            writer.close()
            samtools.index(bam_path)

            bamfile = samtools.alignment_file(bam_path, 'rb')
            actual_aligns = [a for a in bamfile.fetch()]
            bamfile.close()

        align_tags = {}
        for actual_align in actual_aligns:
            for t_name, t_val, t_type  in actual_align.get_tags(with_value_type=True):
                key = (actual_align.query_name, t_name)
                align_tags[key] = "{}:{}:{}".format(t_name, chr(t_type), t_val)

        self.assertEqual(3, len(actual_aligns))
        self.assertEqual("X1:Z:familyA", align_tags[('align1', 'X1')])
        self.assertEqual("X1:Z:familyB", align_tags[('align2', 'X1')])
        self.assertEqual("X1:Z:familyC", align_tags[('align3', 'X1')])
        self.assertEqual("X2:Z:align1", align_tags[('align1', 'X2')])
        self.assertEqual("X2:Z:align2", align_tags[('align2', 'X2')])
        self.assertEqual("X2:Z:align3", align_tags[('align3', 'X2')])

    def test_write_addsHeaderTags(self):
        with TempDirectory() as tmp_dir:
            bam_path = os.path.join(tmp_dir.path, 'destination.bam')
            header = { 'HD': {'VN': '1.0'},
                      'SQ': [{'LN': 1575, 'SN': 'chr1'},
                             {'LN': 1584, 'SN': 'chr2'}] }
            tags = {'X1' : ('Z', lambda family, align: family, 'annotates family'),
                    'X2' : ('Z', lambda family, align: align.query_name, 'annotates query name')}
            writer = samtools.AlignWriter(header, bam_path, tags)
            writer.close()

            bamfile = samtools.alignment_file(bam_path, 'rb')
            actual_header = dict(bamfile.header)
            bamfile.close()

        self.assertEqual(header, actual_header)
