// Runs a child command and reports wall-time and peak RSS.

#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <sys/resource.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#include <string>
#include <vector>

namespace {

struct Options {
  std::string stdout_path;
  std::string stderr_path;
  std::vector<char*> cmd;
};

std::string make_temp_file(const char* prefix) {
  std::string template_path = std::string("/tmp/") + prefix + "XXXXXX";
  std::vector<char> buffer(template_path.begin(), template_path.end());
  buffer.push_back('\0');
  int fd = mkstemp(buffer.data());
  if (fd == -1) {
    return "";
  }
  close(fd);
  return std::string(buffer.data());
}

bool parse_args(int argc, char** argv, Options& options) {
  int i = 1;
  for (; i < argc; ++i) {
    if (std::strcmp(argv[i], "--stdout-path") == 0 && i + 1 < argc) {
      options.stdout_path = argv[++i];
    } else if (std::strcmp(argv[i], "--stderr-path") == 0 && i + 1 < argc) {
      options.stderr_path = argv[++i];
    } else if (std::strcmp(argv[i], "--") == 0) {
      ++i;
      break;
    } else if (std::strcmp(argv[i], "-h") == 0 ||
               std::strcmp(argv[i], "--help") == 0) {
      return false;
    } else {
      break;
    }
  }

  for (; i < argc; ++i) {
    options.cmd.push_back(argv[i]);
  }
  options.cmd.push_back(nullptr);
  if (options.cmd.size() <= 1) {
    return false;
  }
  if (options.stdout_path.empty()) {
    options.stdout_path = make_temp_file("odlt_stdout_");
  }
  if (options.stderr_path.empty()) {
    options.stderr_path = make_temp_file("odlt_stderr_");
  }
  return true;
}

}  // namespace

int main(int argc, char** argv) {
  Options options;
  if (!parse_args(argc, argv, options)) {
    std::fprintf(stderr,
                 "Usage: odlt_run --stdout-path <file> --stderr-path <file> "
                 "-- <command> [args...]\n");
    return 2;
  }

  int stdout_fd = open(options.stdout_path.c_str(),
                       O_CREAT | O_WRONLY | O_TRUNC, 0644);
  int stderr_fd = open(options.stderr_path.c_str(),
                       O_CREAT | O_WRONLY | O_TRUNC, 0644);
  if (stdout_fd == -1 || stderr_fd == -1) {
    std::perror("open");
    return 3;
  }

  auto start = std::chrono::steady_clock::now();
  pid_t pid = fork();
  if (pid == -1) {
    std::perror("fork");
    return 4;
  }
  if (pid == 0) {
    dup2(stdout_fd, STDOUT_FILENO);
    dup2(stderr_fd, STDERR_FILENO);
    close(stdout_fd);
    close(stderr_fd);
    execvp(options.cmd[0], options.cmd.data());
    _exit(127);
  }

  close(stdout_fd);
  close(stderr_fd);

  int status = 0;
  waitpid(pid, &status, 0);
  auto end = std::chrono::steady_clock::now();
  std::chrono::duration<double> elapsed = end - start;

  struct rusage usage {};
  getrusage(RUSAGE_CHILDREN, &usage);

  int exit_code = -1;
  int term_signal = 0;
  if (WIFEXITED(status)) {
    exit_code = WEXITSTATUS(status);
  } else if (WIFSIGNALED(status)) {
    exit_code = 128 + WTERMSIG(status);
    term_signal = WTERMSIG(status);
  }

  std::printf("{\"exit_code\":%d,\"signal\":%d,\"wall_time_sec\":%.6f,"
              "\"max_rss_bytes\":%ld,"
              "\"stdout_path\":\"%s\",\"stderr_path\":\"%s\"}\n",
              exit_code,
              term_signal,
              elapsed.count(),
              static_cast<long>(usage.ru_maxrss),
              options.stdout_path.c_str(),
              options.stderr_path.c_str());
  return 0;
}
