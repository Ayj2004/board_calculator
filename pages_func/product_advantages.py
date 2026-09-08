import streamlit as st
import pandas as pd
from database.crud import get_all_advantages, add_advantage, update_advantage_field, delete_advantage


def page_advantages():
    st.title("✨产品优势管理与查阅")

    tabs = st.tabs(["全部", "长城板", "围栏板", "地板", "通用"])
    cat_list = ["全部", "长城板", "围栏板", "地板", "通用"]

    for idx, cat in enumerate(cat_list):
        with tabs[idx]:
            filter_cat = None if cat == "全部" else cat
            adv_data = get_all_advantages(category=filter_cat)

            if not adv_data:
                st.info("暂无优势记录")
                continue

            for item in adv_data:
                item_id = item["id"]
                with st.container(border=True):
                    st.markdown(f"**【{item['category']}】 {item['title']}**")
                    st.write(item["content"])

                    col_copy, col_edit, col_del = st.columns([4, 1, 1])
                    # 复制按钮
                    btn_key_copy = f"copy_tab{idx}_{item_id}"
                    if col_copy.button(f"📋复制文本:{item['title']}", key=btn_key_copy):
                        st.code(f"{item['title']}\n{item['content']}", language="text")

                    # 编辑按钮，展开编辑表单
                    btn_key_edit = f"edit_tab{idx}_{item_id}"
                    if col_edit.button("✏️编辑", key=btn_key_edit):
                        st.session_state[f"open_edit_{item_id}"] = True

                    # 删除按钮
                    btn_key_del = f"del_tab{idx}_{item_id}"
                    if col_del.button("🗑️删除", key=btn_key_del):
                        st.session_state[f"confirm_del_{item_id}"] = True

                    # =========编辑展开区域=========
                    if st.session_state.get(f"open_edit_{item_id}", False):
                        with st.expander("🔧编辑这条优势", expanded=True):
                            edit_cat = st.selectbox("所属品类",
                                                    ["长城板", "围栏板", "地板", "通用"],
                                                    index=["长城板", "围栏板", "地板", "通用"].index(item["category"]),
                                                    key=f"edit_cat_{item_id}")
                            edit_title = st.text_input("优势标题", value=item["title"], key=f"edit_title_{item_id}")
                            edit_content = st.text_area("优势正文", value=item["content"], key=f"edit_content_{item_id}")
                            edit_sort = st.number_input("排序sort_order", value=item["sort_order"], step=1,
                                                        key=f"edit_sort_{item_id}")

                            col_save, col_cancel = st.columns([1, 1])
                            if col_save.button("💾保存修改", key=f"save_edit_{item_id}"):
                                try:
                                    update_advantage_field(item_id, "category", edit_cat)
                                    update_advantage_field(item_id, "title", edit_title.strip())
                                    update_advantage_field(item_id, "content", edit_content.strip())
                                    update_advantage_field(item_id, "sort_order", int(edit_sort))
                                    st.session_state[f"open_edit_{item_id}"] = False
                                    st.success("✅修改完成！")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"修改失败：{e}")

                            if col_cancel.button("❌取消", key=f"cancel_edit_{item_id}"):
                                st.session_state[f"open_edit_{item_id}"] = False
                                st.rerun()

                    # =========删除二次确认=========
                    if st.session_state.get(f"confirm_del_{item_id}", False):
                        st.warning(f"⚠️确认要删除【{item['title']}】吗？删除后不可恢复！")
                        col_yes, col_no = st.columns([1, 1])
                        if col_yes.button("✅确认删除", key=f"yes_del_{item_id}"):
                            delete_advantage(item_id)
                            del st.session_state[f"confirm_del_{item_id}"]
                            st.success("已删除")
                            st.rerun()
                        if col_no.button("🚫取消删除", key=f"no_del_{item_id}"):
                            del st.session_state[f"confirm_del_{item_id}"]
                            st.rerun()

    st.divider()
    st.subheader("➕新增一条产品优势")
    with st.form("form_adv", clear_on_submit=True):
        cat_in = st.selectbox("所属品类", ["长城板", "围栏板", "地板", "通用"])
        title_in = st.text_input("优势标题")
        content_in = st.text_area("优势正文")
        sort_in = st.number_input("排序sort_order", value=0, step=1)
        subm = st.form_submit_button("新增一条优势")
        if subm:
            if not title_in.strip() or not content_in.strip():
                st.error("标题和正文不能为空！")
            else:
                add_advantage({
                    "category": cat_in,
                    "title": title_in.strip(),
                    "content": content_in.strip(),
                    "sort_order": sort_in
                })
                st.success("✅新增完成，自动刷新")
                st.rerun()


page_advantages()
