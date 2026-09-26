import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from tggo.files import FileInfo
from tggo.planner import split_message, build_plan


class PlannerTests(unittest.TestCase):
    def info(self,name,kind): return FileInfo(Path(name),name,10,"application/octet-stream",kind,"a"*64)
    def test_splits_long_text(self): self.assertEqual([3500,3500,1],[len(x) for x in split_message("x"*7001)])
    def test_groups_photos(self):
        plan=build_plan("caption",[self.info("a.jpg","photo"),self.info("b.jpg","photo")])
        self.assertEqual("media_group",plan[0]["kind"])
    def test_moves_long_caption_to_text(self):
        plan=build_plan("x"*1025,[self.info("a.pdf","document")])
        self.assertEqual("",plan[0]["caption"]); self.assertEqual("text",plan[1]["kind"])
