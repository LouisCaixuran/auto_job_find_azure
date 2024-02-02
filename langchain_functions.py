from langchain.document_loaders import DirectoryLoader, PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import AzureOpenAIEmbeddings as OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.chat_models import AzureChatOpenAI as ChatOpenAI
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv
from config import *


os.environ["OPENAI_API_TYPE"] = "azure"
os.environ["OPENAI_API_VERSION"] = OPENAI_VERSION
os.environ["AZURE_OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["AZURE_OPENAI_ENDPOINT"] = OPENAI_BASE_URL
load_dotenv()
assistant_instructions = """
    本助手将扮演一位求职者的角色，根据上传的pdf简历以及应聘工作的描述，来直接给HR写一个礼貌专业的求职新消息，要求能够用专业的语言结合简历中的经历和技能，并结合应聘工作的描述，来阐述自己的优势，尽最大可能打动招聘者。并且请您始终使用中文来进行消息的编写,开头是招聘负责人，结尾是真诚的，付尧全。这是一封完整的求职信，不要包含求职信内容以外的东西，例如“根据您上传的求职要求和个人简历，我来帮您起草一封求职邮件：”这一类的内容，以便于我直接自动化复制粘贴发送
"""

# 判断是否使用langchain。如果设置了自定义的api地址，则使用langchain
def should_use_langchain():
    should_use_langchain = OPENAI_BASE_URL is not None
    return should_use_langchain

# 读取简历数据
def read_resumes():
    # 读取resume文件夹中的所有文件
    d_loader = DirectoryLoader("./resume", glob="*.pdf",loader_cls=PyPDFLoader)

    # 获取 PDF 文本，返回一个列表，列表中的每个元素都是一个 PDF 文档的页
    pdf_pages = d_loader.load()

    resume_text = ""

    for page in pdf_pages:
        # 建立路径，用于区分是哪一份简历
        # print(page.metadata.get('source'))

        page_text = page.page_content
        resume_text += page_text

    return resume_text

# 文本分割
def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=2000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

# 向量化，并且返回向量存储库
def get_vectorstore(text_chunks):
    embeddings = OpenAIEmbeddings()
    # embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore

# 生成求职信
def generate_letter(vectorstore, job_description):
    # 字数限制
    character_limit = 300
    letter=""
    try:
        langchain_prompt_template = f"""
            你将扮演一位求职者的角色,根据上下文里的简历内容以及应聘工作的描述,来直接给HR写一个礼貌专业, 且字数严格限制在{character_limit}以内的求职消息,要求能够用专业的语言结合简历中的经历和技能,并结合应聘工作的描述,来阐述自己的优势,尽最大可能打动招聘者。始终使用中文来进行消息的编写。开头是招聘负责人, 结尾附上求职者联系方式。这是一份求职消息，不要包含求职内容以外的东西,例如“根据您上传的求职要求和个人简历,我来帮您起草一封求职邮件：”这一类的内容，以便于我直接自动化复制粘贴发送。
            工作描述
            {job_description}"""+"""
            简历内容:
            {context}
            要求:
            {question} 
        """

        question = assistant_instructions
        PROMPT = PromptTemplate.from_template(langchain_prompt_template)
        llm = ChatOpenAI(temperature=1.0,
                        openai_api_version=OPENAI_VERSION,
                        openai_api_key=OPENAI_API_KEY,
                        openai_api_type="azure",
                        azure_deployment=OPENAI_DEPLOYMENT,)
        qa_chain = RetrievalQA.from_chain_type(
            llm, 
            retriever=vectorstore.as_retriever(),
            # return_source_documents=True,
            chain_type_kwargs={"prompt": PROMPT}
        )

        result = qa_chain({"query": question})
        letter = result['result']
        #去掉所有换行符，防止分成多段消息
        letter = letter.replace('\n', ' ')
    except Exception as e:
        print(f"An error occurred: {e}")

    return letter
