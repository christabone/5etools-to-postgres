# Contributing to 5etools-to-postgres

Thank you for your interest in contributing! This project welcomes contributions from the community.

## How to Contribute

### Reporting Issues

If you find a bug or have a feature request:

1. Check if the issue already exists in [GitHub Issues](https://github.com/christabone/5etools-to-postgres/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - Your environment (OS, Python version, PostgreSQL version)
   - Relevant logs or error messages

### Pull Requests

1. **Fork the repository** and create a feature branch
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the project conventions:
   - Python code follows PEP 8 style guidelines
   - SQL uses lowercase table/column names with underscores
   - Add docstrings to new functions
   - Update documentation if needed

3. **Test your changes**:
   ```bash
   # Run validation
   python3 validate_import.py -v
   
   # Run tests
   ./run_tests.sh -v
   
   # Test the pipeline
   python3 run_pipeline.py --mode dry-run
   ```

4. **Commit your changes** with clear messages:
   ```bash
   git commit -m "Add feature: brief description"
   ```

5. **Push to your fork** and create a pull request:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Describe your PR** with:
   - What problem it solves
   - How it was tested
   - Any breaking changes
   - Screenshots (if UI/output related)

### Development Setup

```bash
# Clone your fork
git clone https://github.com/christabone/5etools-to-postgres.git
cd 5etools-to-postgres

# Install dependencies
sudo apt-get install postgresql python3 python3-pytest python3-pytest-benchmark

# Set up database
sudo -u postgres psql -c "CREATE DATABASE dnd5e_reference_dev;"

# Run pipeline
python3 run_pipeline.py --mode full --drop --skip-analysis --verbose
```

## Areas for Contribution

### High Priority
- Additional entity types (classes, races, backgrounds, feats)
- Full-text search optimization
- Performance improvements
- Additional test coverage
- Bug fixes

### Documentation
- Improve existing docs
- Add examples and tutorials
- Create visualization guides
- Document common queries

### Data Quality
- Improve extraction patterns
- Add validation rules
- Report data inconsistencies
- Suggest schema improvements

### Tooling
- Web UI for pipeline monitoring
- Data visualization tools
- Integration examples
- API wrappers

## Code Review Process

1. PRs require at least one review
2. All tests must pass
3. Code must follow project conventions
4. Documentation must be updated
5. No merge conflicts

## Questions?

- Open a [discussion](https://github.com/christabone/5etools-to-postgres/discussions)
- Check existing documentation in `docs/`
- Review [QUICKSTART.md](QUICKSTART.md) and [TESTING.md](TESTING.md)

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the problem, not the person
- Help others learn and grow

## Attribution

Contributors will be recognized in releases and the README.

Thank you for contributing! 🎲✨
