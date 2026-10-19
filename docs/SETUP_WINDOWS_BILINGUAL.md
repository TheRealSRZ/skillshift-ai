# VS Code + GitHub setup | VS Code 与 GitHub 安装步骤

1. **GitHub:** Create a new repository named `skillshift-ai` (initially empty, no README or .gitignore). / 在 GitHub 新建 `skillshift-ai` 空仓库，暂时不要自动生成 README。
2. **Get starter:** Extract the ZIP into a folder named `skillshift-ai` and open it in VS Code. / 解压 ZIP，然后在 VS Code 打开文件夹。
3. **Git setup:** In VS Code Terminal, verify `git --version` and `python --version`. / 打开 Terminal 检查 Git 和 Python 是否正常。
4. **Connect remote:** Replace `YOUR_ORG_OR_USER` with your repository owner. / 将示例仓库名换成真正的地址。

```powershell
git init
git branch -M main
git add .
git commit -m "chore: add SkillShift starter scaffold"
git remote add origin https://github.com/YOUR_ORG_OR_USER/skillshift-ai.git
git push -u origin main
```

5. **Team:** Invite the other 3 GitHub usernames in repository collaborators. / 在 GitHub 邀请其他三位队友作为 Collaborators。
6. **Branch:** Each member clones and creates only their own branch. / 每位成员自行 clone，并建立自己的分支。

```powershell
git clone https://github.com/YOUR_ORG_OR_USER/skillshift-ai.git
cd skillshift-ai
git switch -c ai             # Member 3 example / 第三位成员示例
git push -u origin ai
```

7. **Backend:** Run the environment setup commands in the root README. / 根据 README 运行后端。
8. **Frontend:** Run `npm install` then `npm run dev` inside `frontend/`. / 进入 frontend 安装并运行网页。
9. **Secrets:** Copy `.env.example` to `.env`, populate locally; never commit it. / 将 `.env.example` 复制为 `.env`，仅在本地填写密钥，不上传。
10. **Pull requests:** Merge to `main` only after one other member has reviewed. / 所有代码都通过 Pull Request 审查后才合并。

## If GitHub repo already contains a README / 如果 GitHub 仓库已有 README

Avoid force-pushing or overwriting other members' work. Clone the repository first and copy the starter files into that clone, preferably on a new branch, then open a pull request. / 不要强制覆盖已有代码；先 clone，再把结构复制进去，创建 PR。
