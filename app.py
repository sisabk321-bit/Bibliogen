import streamlit as st
from database import initialize_database, seed_demo_books, get_all_books, add_book, count_books
from rag import BibliogenRAG

st.set_page_config(page_title="Bibliogen", page_icon="📚", layout="wide")
st.markdown("""<style>.main{direction:rtl}h1,h2,h3,p,label{direction:rtl;text-align:right}.title{text-align:center;font-size:42px;font-weight:bold}.subtitle{text-align:center;font-size:18px;margin-bottom:25px}</style>""",unsafe_allow_html=True)

initialize_database(); seed_demo_books()
st.markdown('<div class="title">📚 Bibliogen</div>',unsafe_allow_html=True)
st.markdown('<div class="subtitle">نظام الاسترجاع الذكي للمعلومات الببليوغرافية</div>',unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ إعدادات")
    api_key=st.text_input("OpenAI API Key",type="password")
    st.divider(); st.metric("عدد السجلات",count_books())
    if api_key:
        try: st.metric("عدد المتجهات",BibliogenRAG(api_key).vector_count())
        except Exception as e: st.error(str(e))

tab1,tab2,tab3,tab4=st.tabs(["🔎 الاسترجاع الذكي","📚 فهرس المكتبة","➕ إضافة سجل","ℹ️ عن النظام"])

with tab1:
    st.header("🔎 الاسترجاع الذكي")
    q=st.text_area("اكتب سؤالك:",placeholder="مثال: ما الكتب المتعلقة بعلم المكتبات؟",height=100)
    n=st.slider("عدد المصادر المسترجعة",1,10,5)
    if st.button("🔍 بحث",type="primary",use_container_width=True):
        if not api_key: st.warning("أدخل OpenAI API Key من القائمة الجانبية.")
        elif not q.strip(): st.warning("اكتب سؤالًا أولًا.")
        else:
            try:
                with st.spinner("جاري الاسترجاع..."):
                    rag=BibliogenRAG(api_key)
                    if rag.vector_count()==0: rag.index_all_books()
                    result=rag.answer(q,n)
                st.subheader("💬 الإجابة"); st.write(result["answer"])
                st.divider(); st.subheader("📚 المصادر المسترجعة")
                docs=result["results"].get("documents",[[]])[0]
                metas=result["results"].get("metadatas",[[]])[0]
                dists=result["results"].get("distances",[[]])[0]
                for i,doc in enumerate(docs):
                    m=metas[i] if i<len(metas) else {}
                    with st.container(border=True):
                        st.markdown(f"### {i+1}. {m.get('title','بدون عنوان')}")
                        st.write(f"**المؤلف:** {m.get('author','غير محدد')}")
                        st.write(f"**السنة:** {m.get('publication_year','')}")
                        st.write(f"**الموضوع:** {m.get('subject','')}")
                        if i<len(dists): st.caption(f"مسافة الاسترجاع: {dists[i]:.4f}")
            except Exception as e:
                st.error("حدث خطأ أثناء التشغيل."); st.exception(e)

with tab2:
    st.header("📚 فهرس المكتبة")
    for b in get_all_books():
        with st.expander(f"📖 {b['title']}"):
            for label,key in [("المؤلف","author"),("الناشر","publisher"),("سنة النشر","publication_year"),("الموضوع","subject"),("ISBN","isbn"),("اللغة","language"),("الكلمات المفتاحية","keywords")]:
                st.write(f"**{label}:** {b[key]}")

with tab3:
    st.header("➕ إضافة سجل ببليوغرافي")
    with st.form("add_book"):
        title=st.text_input("العنوان *"); author=st.text_input("المؤلف"); publisher=st.text_input("الناشر")
        year=st.number_input("سنة النشر",0,2100,2025); subject=st.text_input("الموضوع")
        isbn=st.text_input("ISBN"); language=st.text_input("اللغة","العربية")
        typ=st.selectbox("نوع المورد",["كتاب","مقال","رسالة جامعية","مجلة","وثيقة","مورد إلكتروني"])
        keywords=st.text_input("الكلمات المفتاحية")
        submit=st.form_submit_button("💾 حفظ",use_container_width=True)
        if submit:
            if not title.strip(): st.error("العنوان مطلوب.")
            else:
                bid=add_book(title,author,publisher,year,subject,isbn,language,typ,keywords)
                st.success(f"تم حفظ السجل رقم {bid}.")
                if api_key:
                    with st.spinner("جاري فهرسة السجل..."):
                        BibliogenRAG(api_key).index_book({"id":bid,"title":title,"author":author,"publisher":publisher,"publication_year":year,"subject":subject,"isbn":isbn,"language":language,"resource_type":typ,"keywords":keywords})
                    st.success("تم تحويل السجل إلى Vector وفهرسته.")

with tab4:
    st.header("ℹ️ عن Bibliogen")
    st.write("نموذج أولي لنظام استرجاع ذكي للمعلومات الببليوغرافية.")
    st.markdown("السجل الببليوغرافي → Embedding → Vector Database → RAG → LLM → الإجابة + المصادر")
