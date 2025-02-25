from spider.ACM_spider import ACM_spider
from spider.ACL_spider import ACL_spider
from spider.IJCAI_spider import IJCAI_spider
from spider.AAAI_spider import AAAI_spider
from spider.NeurIPS_spider import NeurIPS_spider
from spider.ICLR_spider import ICLR_spider
from spider.ICML_spider import ICML_spider


PROCEEDINGS = [
    ("https://dl.acm.org/conference/recsys/proceedings", "RecSys", "ACM Conference On Recommender Systems", ACM_spider),
    ("https://dl.acm.org/conference/kdd/proceedings", "KDD", "Knowledge Discovery and Data Mining", ACM_spider),
    ("https://dl.acm.org/conference/cikm/proceedings", "CIKM", "Conference on Information and Knowledge Management", ACM_spider),
    ("https://dl.acm.org/conference/ir/proceedings", "SIGIR", "Research and Development in Information Retrieval", ACM_spider),
    ("https://dl.acm.org/conference/umap/proceedings", "UMAP", "User Modeling, Adaptation and Personalization", ACM_spider),
    ("https://dl.acm.org/conference/thewebconf/proceedings", "WWW", "The ACM Web Conference", ACM_spider),
    ("https://dl.acm.org/conference/wsdm/proceedings", "WSDM", "Web Search and Data Mining", ACM_spider),

    ("https://aclanthology.org/venues/eacl/", "EACL", "European Chapter of the Association for Computational Linguistics", ACL_spider),
    ("https://aclanthology.org/venues/naacl/", "NAACL", "North American Chapter of the Association for Computational Linguistics", ACL_spider),
    ("https://aclanthology.org/venues/acl/", "ACL", "Annual Meeting of the Association for Computational Linguistics", ACL_spider),
    ("https://aclanthology.org/venues/emnlp/", "EMNLP", "Conference on Empirical Methods in Natural Language Processing", ACL_spider),

    ("https://ojs.aaai.org/index.php/AAAI/issue/archive", "AAAI", "Association for the Advancement of Artificial Intelligence", AAAI_spider),
    ("https://www.ijcai.org/all_proceedings", "IJCAI", "International Joint Conferences on Artificial Intelligence", IJCAI_spider),
    ("https://papers.nips.cc/", "NeurIPS", "Conference on Neural Information Processing System", NeurIPS_spider),
    ("https://dblp.org/db/conf/iclr/index.html", "ICLR", "International Conference on Learning Representations", ICLR_spider),
    ("https://dblp.org/db/conf/icml/index.html", "ICML", "International Conference on Machine Learning", ICML_spider)
]

# Initial keywords before augmentation
INITIAL_KEYWORDS = [
    ["LLM", "Large Language Model", "Language Model"],
    ["Recommender System", "Recommend"],
    ["Information Retrieval"]
]

# After augmentation, this will be replaced at runtime
AUGMENTED_KEYWORDS = None
